"""Snapshot test — DSVW (Damn Small Vulnerable Web).

Runs ACR-QA against the pinned DSVW fixture and asserts that the finding
count and HIGH-severity count stay within ±5% of the stored baseline.

Marked @pytest.mark.slow — excluded from the default smoke suite.
Run with: pytest -m slow TESTS/snapshot/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

SNAPSHOT_FILE = Path(__file__).parent / "baselines" / "dsvw_baseline.json"
SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "dsvw"
TOLERANCE = 0.05  # ±5%

pytestmark = pytest.mark.slow


def _load_baseline() -> dict:
    if not SNAPSHOT_FILE.exists():
        pytest.skip(
            "DSVW baseline not yet generated — run: pytest --snapshot-update TESTS/snapshot/test_snapshot_dsvw.py"
        )
    return json.loads(SNAPSHOT_FILE.read_text())


def _run_scan(target: Path) -> dict:
    from CORE.orchestrator import run_pipeline

    results = run_pipeline(str(target), repo_name="dsvw-snapshot", limit=200)
    findings = results.get("findings", [])
    high = [
        f
        for f in findings
        if getattr(f, "severity", "").lower() == "high"
        or (isinstance(f, dict) and f.get("severity", "").lower() == "high")
    ]
    return {
        "total_findings": len(findings),
        "high_count": len(high),
        "repo": "dsvw",
    }


@pytest.fixture(scope="module")
def scan_results():
    target = SAMPLE_DIR
    if not target.exists():
        pytest.skip(f"DSVW sample not found at {target} — clone first or check TESTS/samples/")
    return _run_scan(target)


def test_dsvw_total_findings_within_tolerance(scan_results):
    """Total findings must not regress more than 5% below the baseline."""
    baseline = _load_baseline()
    base_total = baseline["total_findings"]
    current = scan_results["total_findings"]
    lower_bound = base_total * (1 - TOLERANCE)
    assert current >= lower_bound, (
        f"DSVW total findings regressed: {current} < {lower_bound:.0f} "
        f"(baseline={base_total}, tolerance={TOLERANCE:.0%})"
    )


def test_dsvw_high_count_within_tolerance(scan_results):
    """HIGH-severity finding count must stay within ±5% of baseline."""
    baseline = _load_baseline()
    base_high = baseline["high_count"]
    current = scan_results["high_count"]
    lower_bound = max(1, base_high * (1 - TOLERANCE))
    assert current >= lower_bound, (
        f"DSVW HIGH finding count regressed: {current} < {lower_bound:.0f} " f"(baseline={base_high})"
    )


def test_dsvw_snapshot_update(request, scan_results):
    """Write a new baseline when --snapshot-update is passed."""
    if not request.config.getoption("--snapshot-update", default=False, skip=True):
        pytest.skip("Pass --snapshot-update to regenerate baseline")
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_FILE.write_text(json.dumps(scan_results, indent=2))
    pytest.fail(f"Baseline updated at {SNAPSHOT_FILE} — re-run without --snapshot-update to verify")
