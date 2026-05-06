"""
Regression guard — Layer 1 (static guard).

When a tool emits a rule we don't have in `RULE_MAPPING`, the normalizer
falls back to `CUSTOM-<rule_id>`. Phase 0 baseline (May 6 2026) found 35
of these silently leaking on DVPWA + httpx (UP012, UP028, UP045 — Ruff
pyupgrade rules). Phase 1 mapped them; this test makes sure no future
diff lets the leak return.

Whenever this test fails: open `CORE/engines/normalizer.py` and add a
`<rule_id>: <CANONICAL_ID>` entry to `RULE_MAPPING`, then add a
`<CANONICAL_ID>: <severity>` entry to `RULE_SEVERITY` in
`severity_scorer.py`. The unmapped tool ID is reported in the test
failure message.

See `docs/GOD_MODE_PLAN.md` §9.3.1 for the rationale.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tool intermediate outputs in DATA/outputs/ are shared across scans
# (PHASE_0_BASELINE.md §6.3). Clean between tests to prevent stale-output races.
_TOOL_OUTPUT_FILES = (
    "ruff.json",
    "bandit.json",
    "semgrep.json",
    "vulture.json",
    "radon.json",
    "jscpd.json",
    "eslint.json",
    "semgrep_js.json",
    "npm_audit.json",
)


@pytest.fixture(autouse=True)
def _clean_tool_outputs():
    """Remove stale tool outputs before each test."""
    for name in _TOOL_OUTPUT_FILES:
        (REPO_ROOT / "DATA" / "outputs" / name).unlink(missing_ok=True)
    yield


# DSVW is the smallest vulnerable Python repo (~30s scan, single file)
# and exercises Ruff + Bandit + Semgrep + Vulture + Radon — i.e. enough
# of the pipeline to surface unmapped rules without the latency tax of
# running on Pygoat / VulPy / DVPWA.
DSVW_PATH = REPO_ROOT / "test_targets" / "eval-repos" / "dsvw"


@pytest.mark.slow
def test_no_custom_rules_on_dsvw() -> None:
    """Scan DSVW and assert zero `CUSTOM-*` findings in the output.

    Skipped when test_targets/ is missing (gitignored).
    """
    if not DSVW_PATH.exists():
        pytest.skip(f"DSVW not present at {DSVW_PATH} (test_targets/ is gitignored)")

    proc = subprocess.run(
        [
            ".venv/bin/python3",
            "CORE/main.py",
            "--target-dir",
            str(DSVW_PATH),
            "--no-ai",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    try:
        findings = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"ACR-QA produced unparseable JSON.\n" f"stderr tail:\n{proc.stderr[-2000:]}\n" f"JSON error: {exc}"
        )

    custom = [
        {
            "canonical_id": f.get("canonical_rule_id"),
            "original_id": f.get("original_rule_id"),
            "tool": (f.get("tool_raw") or {}).get("tool_name"),
            "file": f.get("file"),
            "line": f.get("line"),
        }
        for f in findings
        if str(f.get("canonical_rule_id", "")).startswith("CUSTOM-")
    ]

    assert custom == [], (
        f"Found {len(custom)} CUSTOM-* findings — every tool rule must map "
        f"to a canonical ID via RULE_MAPPING in CORE/engines/normalizer.py.\n"
        f"Unmapped findings:\n"
        + "\n".join(
            f"  {c['tool']}::{c['original_id']} → {c['canonical_id']} at {c['file']}:{c['line']}" for c in custom
        )
    )
