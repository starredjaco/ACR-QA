"""
T4.7 Regression Guard — Eval metric floor assertions.

Ensures that future code changes do not silently degrade the evaluation
numbers that are cited in the thesis. Any change that degrades these
thresholds will fail this test and force an explicit decision.

Thresholds are set conservatively BELOW current numbers to avoid flakiness
(e.g. if corpus changes slightly), while still catching genuine regressions.

Markers: these tests are fast (read JSON, no network/scan), but they are
conceptually "integration" since they depend on eval result files being present.
They run by default (no @slow marker), so CI catches regressions immediately.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "TESTS/evaluation/results"

# ── Loaders ──────────────────────────────────────────────────────────────────


def _load(filename: str) -> dict:
    path = RESULTS_DIR / filename
    if not path.exists():
        pytest.skip(f"Eval result file not found: {filename} — run the eval scripts first")
    with open(path) as f:
        return json.load(f)


# ── Precision thresholds (T4.1 ablation + precision_summary) ─────────────────


class TestPrecisionFloor:
    """Precision corpus — ensure we don't regress below these floors."""

    def test_security_tier_conservative_floor(self) -> None:
        """Security-tier conservative precision must be ≥ 20%."""
        d = _load("precision_summary.json")
        prec = d["security_tier_conservative"]["precision"]
        assert prec >= 0.20, (
            f"Security-tier conservative precision regressed: {prec:.3f} < 0.20. "
            f"Check recent changes to triage heuristics or RULE_MAPPING."
        )

    def test_security_tier_optimistic_floor(self) -> None:
        """Security-tier optimistic precision must be ≥ 30%."""
        d = _load("precision_summary.json")
        prec = d["security_tier_optimistic"]["precision"]
        assert prec >= 0.30, f"Security-tier optimistic precision regressed: {prec:.3f} < 0.30."

    def test_hm_total_count_floor(self) -> None:
        """H/M finding count must be ≥ 500 (corpus hasn't shrunk)."""
        d = _load("precision_summary.json")
        count = d["total_high_med_findings"]
        assert count >= 500, (
            f"H/M finding count dropped to {count} < 500. " f"Did the precision corpus or scan configuration change?"
        )

    def test_security_tier_count_floor(self) -> None:
        """Security-tier finding count must be ≥ 150."""
        d = _load("precision_summary.json")
        count = d["security_tier_conservative"]["total"]
        assert count >= 150, f"Security-tier finding count dropped to {count} < 150."


# ── Recall thresholds ─────────────────────────────────────────────────────────


class TestRecallFloor:
    """Recall corpus — ensure CVE detection rate doesn't regress."""

    def test_track1_recall_floor(self) -> None:
        """Track 1 recall must be 100% on detectable CVEs."""
        d = _load("eval_summary.json")
        results = d.get("results", [])
        detectable = [r for r in results if (r.get("acrqa", {}).get("expected") or r.get("expected_count", 0)) > 0]
        if not detectable:
            pytest.skip("No detectable CVE results in eval_summary.json")

        def _is_detected(r: dict) -> bool:
            a = r.get("acrqa", {})
            m = a.get("matched", [])
            matched_n = len(m) if isinstance(m, list) else int(m or 0)
            return matched_n > 0 or a.get("recall") == 1.0

        matched = sum(1 for r in detectable if _is_detected(r))
        recall = matched / len(detectable)
        assert recall == 1.0, (
            f"Track 1 recall regressed: {matched}/{len(detectable)} = {recall:.0%}. "
            f"Check that CVE detection rules are still active."
        )

    def test_track2_detectable_recall_floor(self) -> None:
        """Track 2 detectable recall must be 100%."""
        d = _load("eval_summary.json")
        t2 = d.get("track2_recall", {})
        if not t2:
            pytest.skip("track2_recall not in eval_summary.json")

        detected = t2.get("detectable_detected", 0)
        total = t2.get("detectable_total", 0)
        if total == 0:
            pytest.skip("No detectable Track 2 CVEs recorded")

        recall = detected / total
        assert recall == 1.0, (
            f"Track 2 recall regressed: {detected}/{total} = {recall:.0%}. " f"Check Track 2 CVE detection rules."
        )

    def test_average_recall_floor(self) -> None:
        """Average recall (including TN repos) must remain 1.0."""
        d = _load("eval_summary.json")
        recall = d.get("average_recall")
        if recall is None:
            pytest.skip("average_recall not in eval_summary.json")
        assert recall == 1.0, f"Average recall regressed: {recall}"


# ── Bootstrap CI floor ────────────────────────────────────────────────────────


class TestBootstrapCIFloor:
    """Bootstrap CI — ensure the CI lower bound doesn't fall below thesis claims."""

    def test_sec_tier_conservative_ci_lo_floor(self) -> None:
        """Security-tier conservative CI lower bound must be ≥ 10%."""
        d = _load("bootstrap_ci.json")
        ci_lo = d["metrics"]["sec_conservative"]["ci_95_lo"]
        assert ci_lo >= 0.10, (
            f"Security-tier conservative CI lower bound regressed: {ci_lo:.3f} < 0.10. "
            f"Corpus may have changed substantially."
        )

    def test_sec_tier_optimistic_ci_lo_floor(self) -> None:
        """Security-tier optimistic CI lower bound must be ≥ 20%."""
        d = _load("bootstrap_ci.json")
        ci_lo = d["metrics"]["sec_optimistic"]["ci_95_lo"]
        assert ci_lo >= 0.20, f"Security-tier optimistic CI lower bound regressed: {ci_lo:.3f} < 0.20."

    def test_bootstrap_n_repos_floor(self) -> None:
        """Bootstrap was run over ≥ 25 repos."""
        d = _load("bootstrap_ci.json")
        n = d.get("n_repos_total", 0)
        assert n >= 25, f"Bootstrap ran over only {n} repos; expected ≥ 25."


# ── Ablation study floor ──────────────────────────────────────────────────────


class TestAblationFloor:
    """Ablation study — ensure each rung is consistent with documented results."""

    def test_rung3_security_tier_finding_count_floor(self) -> None:
        """Security-tier (rung 3) must have ≥ 150 findings."""
        d = _load("ablation_results.json")
        rung3 = d["rungs"][3]
        assert rung3["finding_count"] >= 150, f"Rung 3 finding count dropped to {rung3['finding_count']} < 150."

    def test_rung1_hm_count_floor(self) -> None:
        """H/M severity filter (rung 1) must yield ≥ 500 findings."""
        d = _load("ablation_results.json")
        rung1 = d["rungs"][1]
        assert rung1["finding_count"] >= 500, f"Rung 1 H/M count dropped to {rung1['finding_count']} < 500."

    def test_multi_tool_aggregation_breadth(self) -> None:
        """Multi-tool aggregation must cover ≥ 4 distinct tools in H/M tier."""
        d = _load("ablation_results.json")
        tools_with_hm = [t for t in d.get("per_tool_standalone", []) if t["hm_count"] > 0]
        assert len(tools_with_hm) >= 4, (
            f"Only {len(tools_with_hm)} tools have H/M findings; expected ≥ 4. " f"Tool configuration may have changed."
        )


# ── Determinism floor ─────────────────────────────────────────────────────────


class TestDeterminismFloor:
    """Determinism proof — ensure the proof still passes after code changes."""

    def test_finding_determinism_holds(self) -> None:
        """The determinism proof must report is_deterministic=True."""
        d = _load("determinism_proof.json")
        fd = d["finding_determinism"]
        assert fd["is_deterministic"], (
            f"Finding determinism proof FAILED. "
            f"Only-in-run1: {fd['only_in_run1'][:3]}, "
            f"only-in-run2: {fd['only_in_run2'][:3]}, "
            f"attr diffs: {len(fd['attribute_diffs_on_shared'])}. "
            f"Re-run scripts/run_determinism_proof.py to regenerate."
        )

    def test_ecdsa_both_signatures_valid(self) -> None:
        """Both ECDSA signatures must be cryptographically valid."""
        d = _load("determinism_proof.json")
        assert d["ecdsa_determinism"]["both_signatures_valid"], (
            "ECDSA verification failed in determinism proof. " "AttestationEngine signing may be broken."
        )

    def test_attestation_payload_deterministic(self) -> None:
        """Attestation payload (excl. timestamp) must be deterministic."""
        d = _load("determinism_proof.json")
        assert d["attestation_payload_determinism"]["payload_excluding_timestamp_identical"], (
            "Attestation payload is non-deterministic (excl. timestamp). "
            "Check build_attestation() for random/time-dependent fields."
        )

    def test_overall_determinism(self) -> None:
        """Overall determinism verdict must be True."""
        d = _load("determinism_proof.json")
        assert d["overall_deterministic"], (
            "Overall determinism proof FAILED. " "Re-run scripts/run_determinism_proof.py to diagnose."
        )


# ── Dual-corpus floor ─────────────────────────────────────────────────────────


class TestDualCorpusFloor:
    """Dual-corpus confusion matrix — ensure published numbers hold."""

    def test_recall_detectable_floor(self) -> None:
        """Recall on detectable CVEs must be 100%."""
        d = _load("dual_corpus_matrix.json")
        recall = d["dual_corpus_summary"]["recall_metric"]["recall_detectable"]
        assert recall == 1.0, (
            f"Dual-corpus recall dropped to {recall:.0%}. " f"A previously-detected CVE is now being missed."
        )

    def test_precision_security_tier_conservative_floor(self) -> None:
        """Dual-corpus security-tier conservative precision must be ≥ 20%."""
        d = _load("dual_corpus_matrix.json")
        prec = d["dual_corpus_summary"]["precision_metric_security_tier"]["conservative_precision"]
        assert prec >= 0.20, f"Dual-corpus sec-tier conservative precision regressed: {prec:.3f} < 0.20."
