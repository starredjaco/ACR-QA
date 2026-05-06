"""
Layer 5 — Evaluation Benchmarks (recall battery).

This is the test that proves ACR-QA actually finds the bugs it claims to find.
Loads YAML ground truth files in TESTS/evaluation/ground_truth/, runs ACR-QA
against each repo, and asserts that recall on detectable categories meets the
target declared in the YAML.

Findings marked `out_of_scope: <reason>` in the YAML are EXCLUDED from recall
calculation — they document gaps that no Python static analyzer can close
(e.g., credentials in YAML config, CSRF without runtime context).

Marked `slow` so it doesn't run on every PR — invoke with:
    pytest TESTS/evaluation/ -m slow

Or as part of the nightly evaluation in CI.

See `docs/GOD_MODE_PLAN.md` §9.3.5.1 for the design rationale.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GROUND_TRUTH_DIR = Path(__file__).parent / "ground_truth"


def _load_ground_truth(yml_path: Path) -> dict:
    """Load and minimally validate a ground-truth YAML."""
    with open(yml_path) as fp:
        data = yaml.safe_load(fp)
    assert "repo" in data, f"{yml_path}: missing 'repo' field"
    assert "expected_findings" in data, f"{yml_path}: missing 'expected_findings'"
    assert "recall_target" in data, f"{yml_path}: missing 'recall_target'"
    return data


def _detectable_findings(gt: dict) -> list[dict]:
    """Return only findings NOT marked out_of_scope (i.e., what we expect ACR-QA to detect)."""
    return [f for f in gt["expected_findings"] if "out_of_scope" not in f]


def _run_acrqa(target_dir: Path) -> list[dict]:
    """Invoke ACR-QA via subprocess on `target_dir` and return parsed findings.

    Uses --no-ai for speed (no Groq calls). The per-PID findings.json
    written in pipeline.run() is read by stdout via --json.
    """
    proc = subprocess.run(
        [
            ".venv/bin/python3",
            "CORE/main.py",
            "--target-dir",
            str(target_dir),
            "--no-ai",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    # Exit code 1 is expected when the quality gate fails on a vulnerable repo.
    # We only fail the test if the JSON itself is malformed.
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"ACR-QA produced unparseable JSON for {target_dir}.\n"
            f"stderr tail:\n{proc.stderr[-2000:]}\n"
            f"JSON error: {exc}"
        )


def _matches(finding: dict, expected: dict) -> bool:
    """Does this ACR-QA finding satisfy the expected ground-truth entry?

    Match policy:
      - canonical_id (preferred): exact match on canonical_rule_id
      - file: ACR-QA finding's file path ends with the YAML's relative path
    """
    if expected.get("canonical_id") and finding.get("canonical_rule_id") != expected["canonical_id"]:
        return False
    expected_file = expected.get("file")
    if expected_file:
        finding_file = finding.get("file") or finding.get("file_path") or ""
        if not finding_file.endswith(expected_file):
            return False
    return True


def _ground_truth_yamls() -> list[Path]:
    return sorted(GROUND_TRUTH_DIR.glob("*.yml"))


# Use the YAML repo name as the test ID for readable failures.
@pytest.mark.slow
@pytest.mark.parametrize(
    "gt_path",
    _ground_truth_yamls(),
    ids=lambda p: p.stem,
)
def test_recall_meets_target(gt_path: Path) -> None:
    """For each ground-truth YAML, run ACR-QA and assert recall >= target.

    Skipped when the local repo isn't present (test_targets/ is gitignored,
    so CI runners that haven't cloned the repos will skip cleanly).
    """
    gt = _load_ground_truth(gt_path)
    target_dir = REPO_ROOT / gt["local_path"]
    if not target_dir.exists():
        pytest.skip(f"local repo missing: {target_dir} (gitignored test_targets/)")

    detectable = _detectable_findings(gt)
    if not detectable:
        pytest.skip(f"{gt['repo']}: no detectable findings declared")

    findings = _run_acrqa(target_dir)

    # For each expected finding, did ACR-QA produce at least one matching finding?
    hits = []
    misses = []
    for expected in detectable:
        if any(_matches(f, expected) for f in findings):
            hits.append(expected["id"])
        else:
            misses.append(expected["id"])

    recall = len(hits) / len(detectable)
    target = float(gt["recall_target"])

    assert recall >= target, (
        f"{gt['repo']}: recall {recall:.2%} < target {target:.2%}\n"
        f"  hits ({len(hits)}): {hits}\n"
        f"  misses ({len(misses)}): {misses}"
    )


@pytest.mark.slow
def test_smoke_dsvw_recall() -> None:
    """Fast smoke test for the recall harness itself (DSVW is the smallest repo).

    Runs in <30s; suitable for every PR. The full @pytest.mark.slow battery
    runs nightly in CI.
    """
    gt_path = GROUND_TRUTH_DIR / "dsvw.yml"
    if not gt_path.exists():
        pytest.skip("dsvw.yml ground truth missing")
    test_recall_meets_target(gt_path)
