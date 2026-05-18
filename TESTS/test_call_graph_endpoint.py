"""Unit tests for GET /v1/findings/{fid}/call-graph (v5.0.0 Phase A.1)."""

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
    mock_user = {"id": 7, "email": "u@acrqa.local", "role": "member"}
    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    fastapi_app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c, mock_db
    fastapi_app.dependency_overrides.clear()


_SAMPLE_PY = """
from flask import Flask

app = Flask(__name__)


@app.route("/run")
def run_handler():
    return helper(eval_input())


def helper(x):
    return x + 1


def eval_input():
    return eval(get_arg())


def get_arg():
    return "1+1"


def unused_func():
    return helper(99)
""".strip()


class TestCallGraphEndpoint:
    def test_404_when_finding_missing(self, client):
        c, db = client
        db.get_finding_by_id.return_value = None
        r = c.get("/v1/findings/1/call-graph")
        assert r.status_code == 404

    def test_non_python_returns_unsupported(self, client):
        c, db = client
        db.get_finding_by_id.return_value = {
            "id": 1,
            "file_path": "app.js",
            "line_number": 5,
        }
        r = c.get("/v1/findings/1/call-graph")
        assert r.status_code == 200
        body = r.json()
        assert body["unsupported_language"] is True
        assert body["nodes"] == []

    def test_missing_file_returns_empty(self, client):
        c, db = client
        db.get_finding_by_id.return_value = {
            "id": 1,
            "file_path": "/nonexistent/__nope__.py",
            "line_number": 5,
        }
        r = c.get("/v1/findings/1/call-graph")
        assert r.status_code == 200
        body = r.json()
        assert body.get("file_missing") is True
        assert body["nodes"] == []

    def test_returns_nodes_edges_target_for_python(self, client, tmp_path: Path):
        c, db = client
        src = tmp_path / "app.py"
        src.write_text(_SAMPLE_PY)
        # eval(get_arg()) is on the line inside eval_input(); compute that line
        line = next(i + 1 for i, ln in enumerate(_SAMPLE_PY.splitlines()) if "eval(get_arg" in ln)
        db.get_finding_by_id.return_value = {
            "id": 11,
            "file_path": str(src),
            "line_number": line,
        }
        r = c.get("/v1/findings/11/call-graph")
        assert r.status_code == 200
        body = r.json()
        assert body["target"] == "eval_input"
        names = {n["name"] for n in body["nodes"]}
        assert {"run_handler", "helper", "eval_input", "get_arg", "unused_func"}.issubset(names)
        entry = [n for n in body["nodes"] if n["is_entry"]]
        assert any(n["name"] == "run_handler" for n in entry)
        unused = next(n for n in body["nodes"] if n["name"] == "unused_func")
        assert unused["reachable"] is False
        # target highlight
        target = next(n for n in body["nodes"] if n["is_target"])
        assert target["name"] == "eval_input"
        # edges include run_handler -> helper and run_handler -> eval_input
        edges = {(e["source"], e["target"]) for e in body["edges"]}
        assert ("run_handler", "eval_input") in edges
        assert ("eval_input", "get_arg") in edges

    def test_syntax_error_in_file_returns_empty_graph(self, client, tmp_path: Path):
        c, db = client
        bad = tmp_path / "bad.py"
        bad.write_text("def x(:\n    return\n")
        db.get_finding_by_id.return_value = {
            "id": 2,
            "file_path": str(bad),
            "line_number": 1,
        }
        r = c.get("/v1/findings/2/call-graph")
        assert r.status_code == 200
        body = r.json()
        # _build_call_graph returns empty on SyntaxError → no nodes
        assert body["nodes"] == []
