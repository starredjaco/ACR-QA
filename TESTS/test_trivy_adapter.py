"""Tests for the Trivy container/IaC/dependency scanner adapter (Task 12.12)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from CORE.engines.trivy_adapter import TrivyAdapter

# ── helpers ──────────────────────────────────────────────────────────────────


def _make_trivy_vuln_output(cve_id="CVE-2023-1234", severity="HIGH", pkg="requests"):
    """Return a minimal Trivy JSON output string with one vulnerability."""
    return json.dumps(
        {
            "Results": [
                {
                    "Target": "requirements.txt",
                    "Type": "pip",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": cve_id,
                            "PkgName": pkg,
                            "InstalledVersion": "2.28.0",
                            "FixedVersion": "2.31.0",
                            "Severity": severity,
                            "Title": f"Test vuln in {pkg}",
                            "CweIDs": ["CWE-79"],
                        }
                    ],
                }
            ]
        }
    )


def _make_trivy_misconfig_output():
    """Return a Trivy JSON output with an IaC misconfiguration."""
    return json.dumps(
        {
            "Results": [
                {
                    "Target": "Dockerfile",
                    "Type": "dockerfile",
                    "Misconfigurations": [
                        {
                            "ID": "DS002",
                            "Title": "Image user should not be root",
                            "Description": "Running as root is dangerous",
                            "Resolution": "Add USER directive",
                            "Severity": "HIGH",
                            "CauseMetadata": {"StartLine": 5},
                        }
                    ],
                }
            ]
        }
    )


def _make_trivy_secret_output():
    """Return a Trivy JSON output with a detected secret."""
    return json.dumps(
        {
            "Results": [
                {
                    "Target": "app/config.py",
                    "Type": "python",
                    "Secrets": [
                        {
                            "RuleID": "aws-access-key-id",
                            "Title": "AWS Access Key ID",
                            "Match": "AKIA1234567890ABCDEF",
                            "StartLine": 12,
                        }
                    ],
                }
            ]
        }
    )


# ── availability ─────────────────────────────────────────────────────────────


class TestTrivyAvailability:
    def test_available_true_when_trivy_on_path(self):
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            adapter = TrivyAdapter()
        assert adapter.available is True

    def test_available_false_when_trivy_not_on_path(self):
        with patch("shutil.which", return_value=None):
            adapter = TrivyAdapter()
        assert adapter.available is False

    def test_returns_empty_list_when_not_available(self, tmp_path):
        with patch("shutil.which", return_value=None):
            adapter = TrivyAdapter()
        findings = adapter.scan_directory(tmp_path)
        assert findings == []


# ── vulnerability parsing ─────────────────────────────────────────────────────


class TestTrivyVulnerabilityParsing:
    def _run(self, stdout: str, tmp_path: Path) -> list[dict]:
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            adapter = TrivyAdapter()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = stdout
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            return adapter.scan_directory(tmp_path)

    def test_parses_vulnerability(self, tmp_path):
        findings = self._run(_make_trivy_vuln_output(), tmp_path)
        assert len(findings) == 1
        f = findings[0]
        assert f["tool"] == "trivy"
        assert "CVE-2023-1234" in f["canonical_rule_id"]
        assert f["severity"] == "high"
        assert f["category"] == "security"
        assert f["trivy_type"] == "vulnerability"

    def test_severity_mapping_critical(self, tmp_path):
        stdout = _make_trivy_vuln_output(severity="CRITICAL")
        findings = self._run(stdout, tmp_path)
        assert findings[0]["severity"] == "critical"

    def test_severity_mapping_medium(self, tmp_path):
        stdout = _make_trivy_vuln_output(severity="MEDIUM")
        findings = self._run(stdout, tmp_path)
        assert findings[0]["severity"] == "medium"

    def test_message_contains_cve_and_package(self, tmp_path):
        findings = self._run(_make_trivy_vuln_output(), tmp_path)
        msg = findings[0]["message"]
        assert "CVE-2023-1234" in msg
        assert "requests" in msg

    def test_empty_results_returns_empty_list(self, tmp_path):
        stdout = json.dumps({"Results": []})
        findings = self._run(stdout, tmp_path)
        assert findings == []

    def test_malformed_json_returns_empty_list(self, tmp_path):
        findings = self._run("not valid json {{{", tmp_path)
        assert findings == []


# ── IaC misconfiguration parsing ──────────────────────────────────────────────


class TestTrivyMisconfigParsing:
    def _run(self, stdout: str, tmp_path: Path) -> list[dict]:
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            adapter = TrivyAdapter()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = stdout
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            return adapter.scan_directory(tmp_path)

    def test_parses_misconfig(self, tmp_path):
        findings = self._run(_make_trivy_misconfig_output(), tmp_path)
        assert len(findings) == 1
        f = findings[0]
        assert f["trivy_type"] == "misconfig"
        assert "DS002" in f["canonical_rule_id"]

    def test_misconfig_line_number_extracted(self, tmp_path):
        findings = self._run(_make_trivy_misconfig_output(), tmp_path)
        assert findings[0]["line"] == 5


# ── secret parsing ────────────────────────────────────────────────────────────


class TestTrivySecretParsing:
    def _run(self, stdout: str, tmp_path: Path) -> list[dict]:
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            adapter = TrivyAdapter()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = stdout
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            return adapter.scan_directory(tmp_path)

    def test_parses_secret(self, tmp_path):
        findings = self._run(_make_trivy_secret_output(), tmp_path)
        assert len(findings) == 1
        f = findings[0]
        assert f["trivy_type"] == "secret"
        assert f["canonical_rule_id"] == "HARDCODE-001"
        assert f["severity"] == "high"
        assert f["line"] == 12


# ── error handling ─────────────────────────────────────────────────────────────


class TestTrivyErrorHandling:
    def _make_adapter(self) -> TrivyAdapter:
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            return TrivyAdapter()

    def test_timeout_returns_empty_list(self, tmp_path):
        import subprocess

        adapter = self._make_adapter()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("trivy", 120)):
            findings = adapter.scan_directory(tmp_path)
        assert findings == []

    def test_nonzero_exit_code_returns_empty_list(self, tmp_path):
        adapter = self._make_adapter()
        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stdout = ""
        mock_result.stderr = "fatal error"
        with patch("subprocess.run", return_value=mock_result):
            findings = adapter.scan_directory(tmp_path)
        assert findings == []

    def test_exception_returns_empty_list(self, tmp_path):
        adapter = self._make_adapter()
        with patch("subprocess.run", side_effect=OSError("trivy not found")):
            findings = adapter.scan_directory(tmp_path)
        assert findings == []
