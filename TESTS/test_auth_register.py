"""Unit tests for public self-registration and email verification endpoints.

Coverage: POST /v1/auth/register, POST /v1/auth/verify
UI Testing Plan Layer 1 — 5 tests.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient

from FRONTEND.api.deps import get_db
from FRONTEND.api.main import app as fastapi_app

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def client_with_db():
    """TestClient backed by a real in-memory mock DB that tracks execute() calls."""
    mock_db = MagicMock()
    fastapi_app.dependency_overrides[get_db] = lambda: mock_db
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c, mock_db
    fastapi_app.dependency_overrides.clear()


def _db_register_success(mock_db, email: str, code: str = "123456"):
    """Wire mock_db to behave as if registration succeeds (no duplicate)."""
    call_count = [0]

    def execute_side_effect(sql, params=(), fetch=False):
        call_count[0] += 1
        if fetch and "SELECT id FROM users WHERE email" in sql:
            return []  # No existing user
        if "INSERT INTO users" in sql:
            return {"id": 42}  # Simulate RETURNING id
        return None

    mock_db.execute.side_effect = execute_side_effect
    return mock_db


def _db_duplicate(mock_db, email: str):
    """Wire mock_db so the email already exists."""

    def execute_side_effect(sql, params=(), fetch=False):
        if fetch and "SELECT id FROM users WHERE email" in sql:
            return [{"id": 7}]
        return None

    mock_db.execute.side_effect = execute_side_effect


def _db_verify_success(mock_db, email: str, code: str):
    """Wire mock_db for a successful verify flow."""

    def execute_side_effect(sql, params=(), fetch=False):
        if fetch and "SELECT id, email, role, verification_code" in sql:
            return [{"id": 42, "email": email, "role": "member", "verification_code": code}]
        return None

    mock_db.execute.side_effect = execute_side_effect


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_register_success(client_with_db):
    """201 + returns user_id, email, and a 6-digit verification_code."""
    c, mock_db = client_with_db
    _db_register_success(mock_db, "newuser@example.com")

    r = c.post("/v1/auth/register", json={"email": "newuser@example.com", "password": "securepass123"})

    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "newuser@example.com"
    assert "user_id" in data
    assert "verification_code" in data
    assert len(data["verification_code"]) == 6
    assert data["verification_code"].isdigit()


def test_register_duplicate_email(client_with_db):
    """409 when the email is already registered."""
    c, mock_db = client_with_db
    _db_duplicate(mock_db, "taken@example.com")

    r = c.post("/v1/auth/register", json={"email": "taken@example.com", "password": "securepass123"})

    assert r.status_code == 409
    assert "already" in r.json()["detail"].lower()


def test_register_weak_password(client_with_db):
    """400 when password is shorter than 8 characters."""
    c, mock_db = client_with_db

    r = c.post("/v1/auth/register", json={"email": "weak@example.com", "password": "abc"})

    assert r.status_code == 400
    assert "8" in r.json()["detail"]


def test_register_invalid_email_format(client_with_db):
    """400 when the email address fails basic regex validation."""
    c, mock_db = client_with_db

    for bad_email in ["not-an-email", "missing@", "@nodomain.com"]:
        r = c.post("/v1/auth/register", json={"email": bad_email, "password": "securepass123"})
        assert r.status_code == 400, f"Expected 400 for '{bad_email}', got {r.status_code}"


def test_verify_code_returns_tokens(client_with_db):
    """POST /auth/verify with the correct code returns JWT access + refresh tokens."""
    c, mock_db = client_with_db
    _db_verify_success(mock_db, "verify@example.com", "482910")

    r = c.post("/v1/auth/verify", json={"email": "verify@example.com", "code": "482910"})

    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
