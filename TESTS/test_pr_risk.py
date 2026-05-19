"""Tests for the PR Risk Score (v5.0.0 Phase A.5)."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient

from CORE.engines.pr_risk import (
    HIGH_CAP,
    SIZE_CAP,
    WEIGHTS,
    PRRiskInputs,
    _band,
    inputs_from_findings,
    normalize_inputs,
    predict_pr_risk,
)
from FRONTEND.api.deps import get_current_user, get_db
from FRONTEND.api.main import app as fastapi_app

# ── Catalog / invariants ──────────────────────────────────────────────────────


class TestWeightInvariants:
    def test_weights_sum_to_one(self):
        assert math.isclose(sum(WEIGHTS.values()), 1.0, rel_tol=1e-9)

    def test_weight_keys_complete(self):
        assert set(WEIGHTS) == {
            "high_count",
            "reachability_gate",
            "exploit_verified",
            "taint_touches",
            "file_risk_avg",
            "size_penalty",
        }

    def test_no_single_weight_dominates(self):
        # Nothing >= 0.5 — we want a balanced composition.
        assert max(WEIGHTS.values()) < 0.5


# ── Normalization ─────────────────────────────────────────────────────────────


class TestNormalize:
    def test_zero_inputs_all_zero(self):
        n = normalize_inputs(PRRiskInputs())
        assert all(v == 0.0 for v in n.values())

    def test_max_inputs_all_one(self):
        n = normalize_inputs(
            PRRiskInputs(
                high_count=HIGH_CAP,
                reachable_high_count=HIGH_CAP,
                exploit_verified_count=HIGH_CAP,
                taint_path_count=HIGH_CAP,
                file_risk_scores=[100, 100, 100],
                changed_lines=SIZE_CAP,
            ),
        )
        for v in n.values():
            assert v == 1.0

    def test_reachability_gate_uses_high_fraction(self):
        n = normalize_inputs(PRRiskInputs(high_count=4, reachable_high_count=2))
        assert n["reachability_gate"] == 0.5

    def test_exploit_norm_safe_when_no_high(self):
        n = normalize_inputs(PRRiskInputs(high_count=0, exploit_verified_count=0))
        assert n["exploit_verified"] == 0.0

    def test_size_caps_at_one(self):
        n = normalize_inputs(PRRiskInputs(changed_lines=SIZE_CAP * 5))
        assert n["size_penalty"] == 1.0


# ── Score ─────────────────────────────────────────────────────────────────────


class TestPredict:
    def test_empty_pr_scores_zero(self):
        r = predict_pr_risk(PRRiskInputs())
        assert r.score == 0
        assert r.band == "green"

    def test_full_red_pr_scores_100(self):
        r = predict_pr_risk(
            PRRiskInputs(
                high_count=HIGH_CAP,
                reachable_high_count=HIGH_CAP,
                exploit_verified_count=HIGH_CAP,
                taint_path_count=HIGH_CAP,
                file_risk_scores=[100],
                changed_lines=SIZE_CAP,
            ),
        )
        assert r.score == 100
        assert r.band == "red"

    def test_band_thresholds(self):
        assert _band(0) == "green"
        assert _band(30) == "green"
        assert _band(31) == "amber"
        assert _band(60) == "amber"
        assert _band(61) == "red"
        assert _band(100) == "red"

    def test_size_only_pr_lifts_score_modestly(self):
        # A "huge but clean" PR is still risky to review carelessly — should
        # not be free.
        r = predict_pr_risk(PRRiskInputs(changed_lines=SIZE_CAP))
        # size_penalty weight is 0.15, so a max-size PR alone contributes 15.
        assert 14 <= r.score <= 16

    def test_explainer_calls_out_exploit_verified(self):
        r = predict_pr_risk(
            PRRiskInputs(high_count=1, reachable_high_count=1, exploit_verified_count=1),
        )
        assert any("exploit-verified" in s for s in r.explainer)

    def test_explainer_calls_out_large_pr(self):
        r = predict_pr_risk(PRRiskInputs(changed_lines=200))
        assert any("splitting" in s or "ideal review size" in s for s in r.explainer)

    def test_contribution_breakdown_sums_to_score_over_100(self):
        inp = PRRiskInputs(
            high_count=3,
            reachable_high_count=3,
            exploit_verified_count=1,
            taint_path_count=2,
            file_risk_scores=[40, 70],
            changed_lines=120,
        )
        r = predict_pr_risk(inp)
        assert math.isclose(r.score, round(sum(r.contributions.values()) * 100), abs_tol=1)


# ── inputs_from_findings ─────────────────────────────────────────────────────


class TestInputsFromFindings:
    def test_empty_findings_zero_high(self):
        inp = inputs_from_findings([])
        assert inp.high_count == 0

    def test_high_and_critical_both_count(self):
        findings = [
            {"canonical_severity": "high"},
            {"canonical_severity": "critical"},
            {"canonical_severity": "medium"},
        ]
        assert inputs_from_findings(findings).high_count == 2

    def test_unknown_reachability_treated_as_reachable(self):
        findings = [{"canonical_severity": "high"}]  # no reachability_status
        inp = inputs_from_findings(findings)
        assert inp.reachable_high_count == 1

    def test_dead_code_findings_not_reachable(self):
        findings = [
            {"canonical_severity": "high", "reachability_status": "unreachable"},
            {"canonical_severity": "high", "reachability_status": "reachable"},
        ]
        inp = inputs_from_findings(findings)
        assert inp.reachable_high_count == 1

    def test_exploit_verified_counted(self):
        findings = [
            {"canonical_severity": "high", "exploit_tier": "verified-exploitable"},
            {"canonical_severity": "high", "exploit_tier": "unverified"},
        ]
        inp = inputs_from_findings(findings)
        assert inp.exploit_verified_count == 1

    def test_taint_path_counted(self):
        findings = [
            {"canonical_severity": "high", "taint_path": "request.args → eval"},
            {"canonical_severity": "high", "taint_path": ""},
        ]
        inp = inputs_from_findings(findings)
        assert inp.taint_path_count == 1


# ── Endpoint ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    mock_db = MagicMock()
    mock_user = {"id": 1, "email": "u@x.local", "role": "admin"}
    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    fastapi_app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c, mock_db
    fastapi_app.dependency_overrides.clear()


class TestEndpoint:
    def test_returns_cached_when_present(self, client):
        c, db = client
        db.get_pr_risk_score.return_value = {
            "score": 72,
            "band": "red",
            "high_count": 3,
            "reachable_high_count": 3,
            "exploit_verified_count": 1,
            "taint_path_count": 2,
            "changed_lines": 180,
            "contributions_json": {"high_count": 0.06},
            "explainer_json": ["1 HIGH finding is exploit-verified — do not merge without a fix."],
        }
        r = c.get("/v1/runs/7/pr-risk")
        assert r.status_code == 200
        body = r.json()
        assert body["cached"] is True
        assert body["score"] == 72
        assert body["band"] == "red"

    def test_computes_when_no_cache(self, client):
        c, db = client
        db.get_pr_risk_score.return_value = None
        db.get_findings.return_value = []
        db.get_file_risk_scores.return_value = []
        db.upsert_pr_risk_score.return_value = 1
        r = c.get("/v1/runs/7/pr-risk")
        assert r.status_code == 200
        body = r.json()
        assert body["cached"] is False
        assert body["score"] == 0
        assert body["band"] == "green"

    def test_changed_lines_param_used(self, client):
        c, db = client
        db.get_pr_risk_score.return_value = None
        db.get_findings.return_value = []
        db.get_file_risk_scores.return_value = []
        db.upsert_pr_risk_score.return_value = 1
        r = c.get("/v1/runs/7/pr-risk?changed_lines=250")
        body = r.json()
        # 250 lines / 300 cap = 0.833 normalised → 0.833 * 0.15 weight ≈ 12.5
        assert 10 <= body["score"] <= 14
        assert any("splitting" in s or "lines" in s for s in body["explainer"])

    def test_refresh_forces_recompute(self, client):
        c, db = client
        db.get_pr_risk_score.return_value = {"score": 99, "band": "red"}
        db.get_findings.return_value = []
        db.get_file_risk_scores.return_value = []
        db.upsert_pr_risk_score.return_value = 1
        r = c.get("/v1/runs/7/pr-risk?refresh=true")
        body = r.json()
        assert body["cached"] is False
