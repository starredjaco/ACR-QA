"""Unit tests for GET /v1/runs/{rid}/heatmap (v5.0.0 Phase A.1)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient

from FRONTEND.api.deps import get_current_user, get_db
from FRONTEND.api.main import app as fastapi_app


@pytest.fixture()
def client():
    mock_db = MagicMock()
    mock_user = {"id": 7, "email": "u@acrqa.local", "role": "admin"}
    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    fastapi_app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c, mock_db
    fastapi_app.dependency_overrides.clear()


def _findings():
    return [
        {"file_path": "app/auth.py", "canonical_severity": "high", "canonical_rule_id": "SEC-001"},
        {"file_path": "app/auth.py", "canonical_severity": "high", "canonical_rule_id": "SEC-002"},
        {"file_path": "app/auth.py", "canonical_severity": "medium", "canonical_rule_id": "SEC-001"},
        {"file_path": "app/views.py", "canonical_severity": "medium", "canonical_rule_id": "VAR-001"},
        {"file_path": "app/views.py", "canonical_severity": "low", "canonical_rule_id": "STYLE-001"},
        {"file_path": "utils/db.py", "canonical_severity": "low", "canonical_rule_id": "STYLE-002"},
        {"file_path": "", "canonical_severity": "high"},  # malformed — must be skipped
    ]


class TestHeatmap:
    def test_empty_when_no_findings(self, client):
        c, db = client
        db.get_findings.return_value = []
        r = c.get("/v1/runs/42/heatmap")
        assert r.status_code == 200
        body = r.json()
        assert body == {"run_id": 42, "files": [], "max_high": 0, "max_total": 0}

    def test_groups_by_file(self, client):
        c, db = client
        db.get_findings.return_value = _findings()
        r = c.get("/v1/runs/1/heatmap")
        assert r.status_code == 200
        body = r.json()
        paths = [f["file_path"] for f in body["files"]]
        assert "app/auth.py" in paths
        assert "app/views.py" in paths
        assert "utils/db.py" in paths
        assert "" not in paths

    def test_severity_counts_correct(self, client):
        c, db = client
        db.get_findings.return_value = _findings()
        body = c.get("/v1/runs/1/heatmap").json()
        auth = next(f for f in body["files"] if f["file_path"] == "app/auth.py")
        assert auth["high"] == 2
        assert auth["medium"] == 1
        assert auth["low"] == 0
        assert auth["total"] == 3

    def test_top_rules_sorted(self, client):
        c, db = client
        db.get_findings.return_value = _findings()
        body = c.get("/v1/runs/1/heatmap").json()
        auth = next(f for f in body["files"] if f["file_path"] == "app/auth.py")
        top_ids = [r["rule_id"] for r in auth["top_rules"]]
        assert top_ids[0] == "SEC-001"
        assert auth["top_rules"][0]["count"] == 2

    def test_files_sorted_by_high_then_total(self, client):
        c, db = client
        db.get_findings.return_value = _findings()
        body = c.get("/v1/runs/1/heatmap").json()
        # app/auth.py has 2 HIGH → first
        assert body["files"][0]["file_path"] == "app/auth.py"

    def test_risk_score_in_range_and_high_first(self, client):
        c, db = client
        db.get_findings.return_value = _findings()
        body = c.get("/v1/runs/1/heatmap").json()
        for f in body["files"]:
            assert 0 <= f["risk_score"] <= 100
        # File with HIGH should outrank files without
        auth = next(f for f in body["files"] if f["file_path"] == "app/auth.py")
        views = next(f for f in body["files"] if f["file_path"] == "app/views.py")
        assert auth["risk_score"] > views["risk_score"]

    def test_critical_severity_counted_as_high(self, client):
        c, db = client
        db.get_findings.return_value = [
            {"file_path": "x.py", "canonical_severity": "critical", "canonical_rule_id": "SEC-047"},
        ]
        body = c.get("/v1/runs/1/heatmap").json()
        assert body["files"][0]["high"] == 1
