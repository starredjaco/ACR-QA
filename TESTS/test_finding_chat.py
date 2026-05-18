"""Unit tests for AI Chat Sidebar backend (v5.0.0 Phase A.1).

Coverage:
    GET    /v1/findings/chat/presets
    GET    /v1/findings/{fid}/chat
    POST   /v1/findings/{fid}/chat        (SSE streaming)
    DELETE /v1/findings/{fid}/chat
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient

from FRONTEND.api.deps import get_current_user, get_db
from FRONTEND.api.main import app as fastapi_app
from FRONTEND.api.routers import findings as findings_router

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    mock_db = MagicMock()
    mock_db.get_chat_messages.return_value = []
    mock_db.clear_chat_messages.return_value = 0
    mock_db.insert_chat_message.return_value = 99
    mock_db.get_finding_by_id.return_value = {
        "id": 1,
        "canonical_rule_id": "SECURITY-001",
        "canonical_severity": "high",
        "category": "security",
        "file_path": "app.py",
        "line_number": 42,
        "message": "Use of eval() with attacker-controlled input",
        "code_snippet": "result = eval(request.args['x'])",
    }
    mock_user = {"id": 7, "email": "u@acrqa.local", "role": "member"}

    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    fastapi_app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c, mock_db
    fastapi_app.dependency_overrides.clear()


# ── Presets ───────────────────────────────────────────────────────────────────


class TestChatPresets:
    def test_presets_endpoint_returns_four(self, client):
        c, _ = client
        r = c.get("/v1/findings/chat/presets")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) == 4
        keys = {p["key"] for p in body}
        assert keys == {"explain", "exploit", "pr_comment", "real_in_context"}

    def test_presets_have_label_and_prompt(self, client):
        c, _ = client
        body = c.get("/v1/findings/chat/presets").json()
        for p in body:
            assert p["label"]
            assert p["prompt"]
            assert len(p["prompt"]) > 20

    def test_presets_no_auth_required_for_list(self, client):
        # Currently behind auth via dependency override; just confirm it works.
        c, _ = client
        assert c.get("/v1/findings/chat/presets").status_code == 200


# ── GET history ───────────────────────────────────────────────────────────────


class TestChatHistory:
    def test_list_empty_history(self, client):
        c, db = client
        db.get_chat_messages.return_value = []
        r = c.get("/v1/findings/1/chat")
        assert r.status_code == 200
        assert r.json() == {"finding_id": 1, "messages": []}

    def test_list_returns_messages(self, client):
        c, db = client
        db.get_chat_messages.return_value = [
            {
                "id": 1,
                "finding_id": 1,
                "role": "user",
                "preset": "explain",
                "content": "hi",
                "model_name": None,
                "tokens_in": None,
                "tokens_out": None,
                "latency_ms": None,
                "created_at": "2026-05-18T00:00:00Z",
                "user_id": 7,
            }
        ]
        r = c.get("/v1/findings/1/chat")
        assert r.status_code == 200
        body = r.json()
        assert body["finding_id"] == 1
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][0]["preset"] == "explain"

    def test_list_404_when_finding_missing(self, client):
        c, db = client
        db.get_finding_by_id.return_value = None
        r = c.get("/v1/findings/9999/chat")
        assert r.status_code == 404


# ── DELETE ────────────────────────────────────────────────────────────────────


class TestChatClear:
    def test_delete_clears_history(self, client):
        c, db = client
        db.clear_chat_messages.return_value = 3
        r = c.delete("/v1/findings/1/chat")
        assert r.status_code == 200
        assert r.json() == {"finding_id": 1, "deleted": 3}
        db.clear_chat_messages.assert_called_once_with(1)

    def test_delete_404_when_finding_missing(self, client):
        c, db = client
        db.get_finding_by_id.return_value = None
        r = c.delete("/v1/findings/1/chat")
        assert r.status_code == 404


# ── POST chat ─────────────────────────────────────────────────────────────────


def _fake_stream_chunks(text_parts):
    """Build an iterable mimicking Groq stream chunks with delta.content."""

    class _Delta:
        def __init__(self, content):
            self.content = content

    class _Choice:
        def __init__(self, content):
            self.delta = _Delta(content)

    class _Chunk:
        def __init__(self, content):
            self.choices = [_Choice(content)]

    return [_Chunk(t) for t in text_parts]


class _FakeClient:
    """Mimics groq SDK client.chat.completions.create(stream=True)."""

    def __init__(self, parts):
        self._parts = parts

        class _Completions:
            def __init__(self, outer):
                self._outer = outer

            def create(self, **_kwargs):
                return _fake_stream_chunks(self._outer._parts)

        class _Chat:
            def __init__(self, outer):
                self.completions = _Completions(outer)

        self.chat = _Chat(self)


class _FakeKeyPool:
    has_keys = True

    def __init__(self, parts):
        self._parts = parts

    def next_client(self):
        return _FakeClient(self._parts)


class _FakeEngine:
    def __init__(self, parts):
        self.key_pool = _FakeKeyPool(parts)


class TestChatPost:
    def test_post_requires_preset_or_content(self, client):
        c, _ = client
        r = c.post("/v1/findings/1/chat", json={})
        assert r.status_code == 400

    def test_post_rejects_unknown_preset(self, client):
        c, _ = client
        r = c.post("/v1/findings/1/chat", json={"preset": "no-such-preset"})
        assert r.status_code == 400

    def test_post_404_when_finding_missing(self, client):
        c, db = client
        db.get_finding_by_id.return_value = None
        r = c.post("/v1/findings/1/chat", json={"content": "hi"})
        assert r.status_code == 404

    def test_post_streams_assistant_reply(self, client):
        c, db = client
        with patch.object(
            findings_router,
            "ExplanationEngine",
            create=True,
            return_value=_FakeEngine(["Hel", "lo ", "world"]),
        ):
            # Patch the lazy import inside _stream_assistant_reply:
            with patch(
                "CORE.engines.explainer.ExplanationEngine",
                return_value=_FakeEngine(["Hel", "lo ", "world"]),
            ):
                r = c.post(
                    "/v1/findings/1/chat",
                    json={"content": "Explain this please."},
                )
                assert r.status_code == 200
                body = r.text
                assert "data:" in body
                assert "delta" in body
                assert "done" in body
                assert "Hello world" in body or "Hel" in body
        # Two inserts: user turn + assistant turn
        assert db.insert_chat_message.call_count >= 2

    def test_post_preset_uses_preset_prompt(self, client):
        c, db = client
        with patch(
            "CORE.engines.explainer.ExplanationEngine",
            return_value=_FakeEngine(["ok"]),
        ):
            r = c.post(
                "/v1/findings/1/chat",
                json={"preset": "explain"},
            )
            assert r.status_code == 200
        # First insert should be the user turn with preset='explain'
        first = db.insert_chat_message.call_args_list[0]
        assert first.kwargs.get("preset") == "explain"
        assert first.kwargs.get("role") == "user"

    def test_post_degrades_when_no_keys(self, client):
        c, db = client

        class _EmptyPool:
            has_keys = False

            def next_client(self):
                raise RuntimeError("no keys")

        class _EmptyEngine:
            key_pool = _EmptyPool()

        with patch(
            "CORE.engines.explainer.ExplanationEngine",
            return_value=_EmptyEngine(),
        ):
            r = c.post(
                "/v1/findings/1/chat",
                json={"content": "test"},
            )
        assert r.status_code == 200
        assert "unavailable" in r.text.lower() or "no llm key" in r.text.lower()

    def test_post_handles_stream_failure(self, client):
        c, db = client

        class _BoomClient:
            class _Chat:
                class _Completions:
                    def create(self, **_):
                        raise RuntimeError("boom")

                completions = _Completions()

            chat = _Chat()

        class _BoomPool:
            has_keys = True

            def next_client(self):
                return _BoomClient()

        class _BoomEngine:
            key_pool = _BoomPool()

        with patch(
            "CORE.engines.explainer.ExplanationEngine",
            return_value=_BoomEngine(),
        ):
            r = c.post("/v1/findings/1/chat", json={"content": "test"})
        assert r.status_code == 200
        assert "interrupted" in r.text.lower() or "done" in r.text.lower()


# ── Helpers ───────────────────────────────────────────────────────────────────


class TestHelpers:
    def test_build_system_prompt_contains_rule(self):
        from FRONTEND.api.routers.findings import _build_system_prompt

        prompt = _build_system_prompt(
            {
                "canonical_rule_id": "SEC-001",
                "canonical_severity": "high",
                "category": "security",
                "file_path": "x.py",
                "line_number": 5,
                "message": "danger",
                "code_snippet": "eval(x)",
            }
        )
        assert "SEC-001" in prompt
        assert "x.py" in prompt
        assert "eval(x)" in prompt

    def test_build_system_prompt_handles_missing_fields(self):
        from FRONTEND.api.routers.findings import _build_system_prompt

        prompt = _build_system_prompt({})
        assert "UNKNOWN" in prompt
        assert "<unknown>" in prompt

    def test_sse_formatting(self):
        from FRONTEND.api.routers.findings import _sse

        out = _sse({"event": "delta", "text": "hi"})
        assert out.startswith(b"data: ")
        assert out.endswith(b"\n\n")
        assert b'"event": "delta"' in out

    def test_preset_resolution_prefers_preset(self):
        from FRONTEND.api.routers.findings import (
            ChatPostRequest,
            _resolve_user_content,
        )

        req = ChatPostRequest(preset="explain", content="ignored")
        content, key = _resolve_user_content(req)
        assert key == "explain"
        assert "Explain" in content or "explain" in content.lower()

    def test_preset_resolution_empty_raises(self):
        from fastapi import HTTPException

        from FRONTEND.api.routers.findings import (
            ChatPostRequest,
            _resolve_user_content,
        )

        with pytest.raises(HTTPException):
            _resolve_user_content(ChatPostRequest(content=""))
