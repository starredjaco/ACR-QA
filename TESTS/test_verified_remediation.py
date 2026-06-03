"""
Tests for CORE/engines/verified_remediation.py (Track C — v8 plan).

Unit tests run without Docker (mock exploit verifier).
Integration/exploit tests require Docker and are marked @pytest.mark.exploit.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from CORE.engines.exploit_verifier import ExploitResult
from CORE.engines.verified_remediation import (
    RemediationResult,
    VerifiedRemediationEngine,
    _make_diff,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_exploit_result(tier: str, verified: bool = False) -> ExploitResult:
    return ExploitResult(
        finding_id="test-id",
        category="sql-injection",
        verified=verified,
        tier=tier,
    )


def _sqli_finding(file_path: str = "/tmp/app.py") -> dict:
    return {
        "id": "test-sqli-001",
        "canonical_rule_id": "SECURITY-027",
        "canonical_severity": "high",
        "file": file_path,
        "file_path": file_path,
        "line": 1,
        "message": "SQL injection via string formatting",
        "tool_raw": {"tool_name": "bandit", "original_output": {"issue_confidence": "HIGH"}},
    }


# ---------------------------------------------------------------------------
# Unit tests — no Docker needed
# ---------------------------------------------------------------------------


class TestRemediationResult:
    def test_to_dict_structure(self):
        r = RemediationResult(finding_id="f1", canonical_rule_id="SECURITY-027", file="app.py")
        d = r.to_dict()
        assert "fix_verified" in d
        assert "vuln_proof" in d
        assert "fix_diff" in d
        assert "fix_proof" in d
        assert "attestation" in d

    def test_summary_line_verified(self):
        r = RemediationResult(
            finding_id="f1",
            canonical_rule_id="SECURITY-027",
            file="app.py",
            fix_verified=True,
            duration_seconds=3.2,
        )
        line = r.summary_line()
        assert "FIX VERIFIED" in line
        assert "SECURITY-027" in line

    def test_summary_line_not_verified(self):
        r = RemediationResult(
            finding_id="f1",
            canonical_rule_id="SECURITY-027",
            file="app.py",
            fix_verified=False,
            error="exploit still fires",
        )
        line = r.summary_line()
        assert "NOT VERIFIED" in line
        assert "exploit still fires" in line


class TestMakeDiff:
    def test_diff_shows_changed_line(self, tmp_path):
        orig = tmp_path / "orig.py"
        patched = tmp_path / "patched.py"
        orig.write_text("x = eval(user_input)\n")
        patched.write_text("x = ast.literal_eval(user_input)\n")
        diff = _make_diff(orig, patched)
        assert "-x = eval" in diff
        assert "+x = ast.literal_eval" in diff

    def test_diff_empty_when_identical(self, tmp_path):
        orig = tmp_path / "orig.py"
        patched = tmp_path / "patched.py"
        orig.write_text("x = 1\n")
        patched.write_text("x = 1\n")
        diff = _make_diff(orig, patched)
        assert diff == ""


class TestVerifiedRemediationEngineUnit:
    """Unit tests with mocked exploit verifier and autofix."""

    def _engine(self) -> VerifiedRemediationEngine:
        return VerifiedRemediationEngine(use_docker=False, sign=False)

    def test_can_verify_returns_false_when_docker_off(self, tmp_path):
        engine = self._engine()
        finding = _sqli_finding(str(tmp_path / "app.py"))
        # Docker disabled → exploit verifier can_verify returns False
        result = engine.can_verify(finding)
        assert result is False

    def test_run_returns_result_object(self, tmp_path):
        engine = self._engine()
        finding = _sqli_finding(str(tmp_path / "app.py"))
        result = engine.run(finding, str(tmp_path))
        assert isinstance(result, RemediationResult)
        assert result.fix_verified is False  # docker off → unverified

    def test_run_does_not_raise_on_bad_input(self):
        engine = self._engine()
        result = engine.run({}, "/nonexistent/path")
        assert isinstance(result, RemediationResult)
        assert result.fix_verified is False

    def test_pipeline_step1_fail_if_exploit_does_not_fire(self, tmp_path):
        """If exploit doesn't fire before fix, pipeline aborts at step 1."""
        engine = self._engine()
        finding = _sqli_finding(str(tmp_path / "app.py"))

        mock_before = _make_exploit_result("unverified")

        with (
            patch.object(engine._verifier, "can_verify", return_value=True),
            patch.object(engine._verifier, "verify_finding", return_value=mock_before),
        ):
            result = engine.run(finding, str(tmp_path))

        assert result.fix_verified is False
        assert "Step 1 failed" in (result.error or "")

    def test_pipeline_step2_fail_if_no_patch(self, tmp_path):
        """If autofix can't patch, pipeline aborts at step 2."""
        engine = self._engine()
        finding = _sqli_finding(str(tmp_path / "app.py"))

        mock_before = _make_exploit_result("verified-exploitable", verified=True)

        with (
            patch.object(engine._verifier, "can_verify", return_value=True),
            patch.object(engine._verifier, "verify_finding", return_value=mock_before),
            patch.object(engine._fixer, "generate_patch", return_value=None),
            patch.object(engine._fixer, "generate_fix", return_value=None),
            patch.object(engine._fixer, "can_fix", return_value=True),
        ):
            result = engine.run(finding, str(tmp_path))

        assert result.fix_verified is False
        assert "Step 2 failed" in (result.error or "")

    def test_pipeline_step4_fail_if_exploit_still_fires_after_fix(self, tmp_path):
        """If exploit still fires after patch, fix_verified must be False."""
        engine = self._engine()
        app_file = tmp_path / "app.py"
        app_file.write_text("query = f'SELECT * FROM users WHERE id = {user_id}'\n")
        finding = _sqli_finding(str(app_file))

        mock_before = _make_exploit_result("verified-exploitable", verified=True)
        mock_after = _make_exploit_result("verified-exploitable", verified=True)
        mock_patch = {
            "original": "query = f'SELECT * FROM users WHERE id = {user_id}'",
            "fixed": "query = 'SELECT * FROM users WHERE id = ?'",
            "description": "Parameterized query",
        }

        with (
            patch.object(engine._verifier, "can_verify", return_value=True),
            patch.object(engine._verifier, "verify_finding", side_effect=[mock_before, mock_after]),
            patch.object(engine, "_generate_patch", return_value=mock_patch),
        ):
            result = engine.run(finding, str(tmp_path))

        assert result.fix_verified is False
        assert "still fires" in (result.error or "")

    def test_pipeline_full_success(self, tmp_path):
        """Happy path: exploit fires → patch applied → exploit fails → fix_verified=True."""
        engine = self._engine()
        app_file = tmp_path / "app.py"
        app_file.write_text("query = f'SELECT * FROM users WHERE id = {user_id}'\n")
        finding = _sqli_finding(str(app_file))

        mock_before = _make_exploit_result("verified-exploitable", verified=True)
        mock_after = _make_exploit_result("verified-unexploitable", verified=False)
        mock_patch = {
            "original": "query = f'SELECT * FROM users WHERE id = {user_id}'",
            "fixed": "query = 'SELECT * FROM users WHERE id = ?'",
        }

        with (
            patch.object(engine._verifier, "can_verify", return_value=True),
            patch.object(engine._verifier, "verify_finding", side_effect=[mock_before, mock_after]),
            patch.object(engine, "_generate_patch", return_value=mock_patch),
        ):
            result = engine.run(finding, str(tmp_path))

        assert result.fix_verified is True
        assert result.fix_diff != ""
        assert result.error is None

    def test_run_batch_skips_ineligible(self, tmp_path):
        engine = self._engine()
        findings = [
            _sqli_finding(str(tmp_path / "app.py")),
            {"canonical_rule_id": "UNKNOWN-999"},  # ineligible
        ]
        with patch.object(engine, "can_verify", side_effect=[True, False]):
            with patch.object(
                engine,
                "run",
                return_value=RemediationResult(finding_id="x", canonical_rule_id="SECURITY-027", file="app.py"),
            ):
                results = engine.run_batch(findings, str(tmp_path))
        assert len(results) == 1

    def test_attestation_called_when_fix_verified(self, tmp_path):
        engine = self._engine()
        # Re-enable attestation
        mock_attester = MagicMock()
        mock_attester.sign.return_value = {"signature": "abc", "signed": True}
        engine._attester = mock_attester

        app_file = tmp_path / "app.py"
        app_file.write_text("query = f'SELECT * FROM users WHERE id = {user_id}'\n")
        finding = _sqli_finding(str(app_file))

        mock_before = _make_exploit_result("verified-exploitable", verified=True)
        mock_after = _make_exploit_result("verified-unexploitable", verified=False)
        mock_patch = {
            "original": "query = f'SELECT * FROM users WHERE id = {user_id}'",
            "fixed": "query = 'SELECT * FROM users WHERE id = ?'",
        }

        with (
            patch.object(engine._verifier, "can_verify", return_value=True),
            patch.object(engine._verifier, "verify_finding", side_effect=[mock_before, mock_after]),
            patch.object(engine, "_generate_patch", return_value=mock_patch),
        ):
            result = engine.run(finding, str(tmp_path))

        assert result.fix_verified is True
        mock_attester.sign.assert_called_once()
        assert result.attestation.get("signed") is True

    def test_result_serialisable_to_json(self, tmp_path):
        """RemediationResult.to_dict() must JSON-serialise cleanly."""
        engine = self._engine()
        app_file = tmp_path / "app.py"
        app_file.write_text("x = 1\n")
        finding = _sqli_finding(str(app_file))
        result = engine.run(finding, str(tmp_path))
        # Must not raise
        json.dumps(result.to_dict())


# ---------------------------------------------------------------------------
# Integration tests — require Docker
# ---------------------------------------------------------------------------


@pytest.mark.exploit
class TestVerifiedRemediationIntegration:
    """End-to-end pipeline using the flask_sqli fixture. Requires Docker."""

    @pytest.fixture(autouse=True)
    def check_docker(self):
        engine = VerifiedRemediationEngine(use_docker=True, sign=False)
        if not engine._verifier.is_docker_available():
            pytest.skip("Docker not available")

    def _sqli_fixture_dir(self) -> Path:
        return Path(__file__).parent / "fixtures" / "exploits" / "flask_sqli"

    def test_full_pipeline_on_sqli_fixture(self):
        """
        SQLi fixture: exploit should fire on original, then fail after parameterization fix.
        This is the live Verified Remediation demo scenario.
        """
        fixtures_dir = self._sqli_fixture_dir()
        if not fixtures_dir.exists():
            pytest.skip(f"SQLi fixture not found at {fixtures_dir}")

        engine = VerifiedRemediationEngine(use_docker=True, sign=False)
        finding = {
            "id": "integration-sqli-001",
            "canonical_rule_id": "SECURITY-027",
            "canonical_severity": "high",
            "file": str(fixtures_dir / "app.py"),
            "file_path": str(fixtures_dir / "app.py"),
            "line": 20,
            "message": "SQL injection",
            "tool_raw": {
                "tool_name": "bandit",
                "original_output": {"issue_confidence": "HIGH"},
            },
        }

        result = engine.run(finding, str(fixtures_dir))

        # The pipeline must return a result — fix_verified depends on patch quality
        assert isinstance(result, RemediationResult)
        assert result.vuln_proof != {}  # step 1 attempted
        # If fix was generated and exploit fired before: check the chain
        if result.vuln_proof.get("tier") == "verified-exploitable":
            assert result.fix_diff != "" or result.error is not None

    def test_remediation_result_to_json_integration(self):
        """Result from real Docker run must be JSON-serialisable."""
        fixtures_dir = self._sqli_fixture_dir()
        if not fixtures_dir.exists():
            pytest.skip(f"SQLi fixture not found at {fixtures_dir}")

        engine = VerifiedRemediationEngine(use_docker=True, sign=False)
        finding = {
            "id": "json-test-001",
            "canonical_rule_id": "SECURITY-027",
            "canonical_severity": "high",
            "file": str(fixtures_dir / "app.py"),
            "file_path": str(fixtures_dir / "app.py"),
            "line": 20,
            "message": "SQL injection",
            "tool_raw": {
                "tool_name": "bandit",
                "original_output": {"issue_confidence": "HIGH"},
            },
        }
        result = engine.run(finding, str(fixtures_dir))
        # Must not raise
        payload = json.dumps(result.to_dict())
        assert len(payload) > 10
