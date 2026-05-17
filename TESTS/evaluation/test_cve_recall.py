"""
test_cve_recall.py — Tier 1 CVE Recall pytest integration.

Parametrised over every YAML in TESTS/evaluation/cve_recall/.
Marked @pytest.mark.slow — NOT run on every PR (too slow).
Run manually or via `make eval-reproduce`.

Usage:
    pytest TESTS/evaluation/test_cve_recall.py -m slow -v

Each test:
  1. Verifies the YAML has pre_registered_sha (pre-registration gate)
  2. If acrqa_detected is already set (from a previous run_cve_recall run),
     asserts the result matches expectations.
  3. If vuln_commit_sha is set but acrqa_detected is not, skips with a message
     prompting to run `python3 scripts/run_cve_recall.py --update`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent
CVE_DIR = ROOT / "TESTS" / "evaluation" / "cve_recall"


def _load_cve_yamls() -> list[dict]:
    paths = sorted(CVE_DIR.glob("*.yml"))
    result = []
    for p in paths:
        if p.name == ".gitkeep":
            continue
        with p.open() as f:
            data = yaml.safe_load(f)
        if data:
            data["_path"] = str(p)
            result.append(data)
    return result


CVE_DATA = _load_cve_yamls()


@pytest.mark.slow
@pytest.mark.parametrize("cve", CVE_DATA, ids=[c.get("cve_id", "unknown") for c in CVE_DATA])
def test_cve_recall(cve: dict) -> None:
    """Each CVE must be pre-registered and, once scanned, detected by ACR-QA."""
    cve_id = cve.get("cve_id", "unknown")

    # Gate 1 — pre-registration
    pre_sha = cve.get("pre_registered_sha", "").strip()
    assert pre_sha and not pre_sha.startswith("<"), (
        f"{cve_id}: missing pre_registered_sha — YAML must be committed "
        f"before scanning to satisfy the pre-registration commitment in INTEGRITY.md"
    )

    # Gate 2 — commit SHA must be set before we can evaluate
    vuln_sha = cve.get("vuln_commit_sha", "").strip()
    if not vuln_sha or vuln_sha.startswith("<"):
        pytest.skip(f"{cve_id}: vuln_commit_sha not set — run " f"`python3 scripts/run_cve_recall.py --update` to scan")

    # Gate 3 — scan result
    detected = cve.get("acrqa_detected")
    if detected is None:
        pytest.skip(
            f"{cve_id}: acrqa_detected not set — run " f"`python3 scripts/run_cve_recall.py --cve {cve_id} --update`"
        )

    # If CWE category is explicitly out_of_scope, skip gracefully
    if cve.get("out_of_scope"):
        pytest.skip(f"{cve_id}: marked out_of_scope — {cve.get('out_of_scope_reason', '')}")

    # The core assertion: ACR-QA detected the CVE
    assert detected is True, (
        f"{cve_id} ({cve.get('project', '?')}): ACR-QA did NOT detect this CVE.\n"
        f"  Affected file:  {cve.get('affected_file', '?')}\n"
        f"  Affected lines: {cve.get('affected_lines', '?')}\n"
        f"  CWE: {cve.get('cwe', '?')}\n"
        f"  Notes: {cve.get('notes', 'none')}\n"
        f"  Action: document miss reason in INTEGRITY.md Skipped-CVE log if this is "
        f"expected (e.g. runtime context required)."
    )
