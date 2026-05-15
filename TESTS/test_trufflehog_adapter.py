"""Tests for the TruffleHog verified secrets adapter (Task 12.13)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from CORE.engines.trufflehog_adapter import TruffleHogAdapter

# ── helpers ──────────────────────────────────────────────────────────────────


def _make_th_line(detector="GitHub", verified=True, raw="ghp_abc123", file="app.py", line=42):
    """Return a single TruffleHog NDJSON line."""
    return json.dumps(
        {
            "DetectorName": detector,
            "Verified": verified,
            "Raw": raw,
            "SourceMetadata": {
                "Data": {
                    "Filesystem": {
                        "file": file,
                        "line": line,
                    }
                }
            },
        }
    )


# ── availability ─────────────────────────────────────────────────────────────


class TestTruffleHogAvailability:
    def test_available_true_when_on_path(self):
        with patch("shutil.which", return_value="/usr/local/bin/trufflehog"):
            adapter = TruffleHogAdapter()
        assert adapter.available is True

    def test_available_false_when_not_on_path(self):
        with patch("shutil.which", return_value=None):
            adapter = TruffleHogAdapter()
        assert adapter.available is False

    def test_returns_empty_when_not_available(self, tmp_path):
        with patch("shutil.which", return_value=None):
            adapter = TruffleHogAdapter()
        assert adapter.scan_directory(tmp_path) == []


# ── parsing ───────────────────────────────────────────────────────────────────


class TestTruffleHogParsing:
    def _run(self, ndjson: str, tmp_path: Path) -> list[dict]:
        with patch("shutil.which", return_value="/usr/local/bin/trufflehog"):
            adapter = TruffleHogAdapter()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ndjson
        with patch("subprocess.run", return_value=mock_result):
            return adapter.scan_directory(tmp_path)

    def test_parses_single_verified_secret(self, tmp_path):
        findings = self._run(_make_th_line(verified=True), tmp_path)
        assert len(findings) == 1
        f = findings[0]
        assert f["tool"] == "trufflehog"
        assert f["canonical_rule_id"] == "HARDCODE-001"
        assert f["severity"] == "high"
        assert f["verified"] is True

    def test_parses_unverified_secret_as_medium(self, tmp_path):
        findings = self._run(_make_th_line(verified=False), tmp_path)
        assert findings[0]["severity"] == "medium"
        assert findings[0]["verified"] is False

    def test_file_and_line_extracted(self, tmp_path):
        findings = self._run(_make_th_line(file="src/config.py", line=99), tmp_path)
        assert findings[0]["file"] == "src/config.py"
        assert findings[0]["line"] == 99

    def test_raw_secret_is_masked_in_message(self, tmp_path):
        findings = self._run(_make_th_line(raw="ghp_supersecret_token_1234"), tmp_path)
        msg = findings[0]["message"]
        # Only first 6 chars should appear; full secret must not be exposed
        assert "ghp_su" in msg
        assert "supersecret_token_1234" not in msg

    def test_detector_name_in_message(self, tmp_path):
        findings = self._run(_make_th_line(detector="AWSAccessKey"), tmp_path)
        msg = findings[0]["message"]
        assert "AWSAccessKey" in msg

    def test_multiple_lines_parsed(self, tmp_path):
        ndjson = "\n".join(
            [
                _make_th_line(detector="GitHub", file="a.py", line=1),
                _make_th_line(detector="Stripe", file="b.py", line=2),
                _make_th_line(detector="AWS", file="c.py", line=3),
            ]
        )
        findings = self._run(ndjson, tmp_path)
        assert len(findings) == 3

    def test_empty_output_returns_empty_list(self, tmp_path):
        findings = self._run("", tmp_path)
        assert findings == []

    def test_non_json_lines_skipped(self, tmp_path):
        ndjson = "not json\n" + _make_th_line() + "\nalso not json"
        findings = self._run(ndjson, tmp_path)
        assert len(findings) == 1


# ── error handling ─────────────────────────────────────────────────────────────


class TestTruffleHogErrorHandling:
    def _make_adapter(self) -> TruffleHogAdapter:
        with patch("shutil.which", return_value="/usr/local/bin/trufflehog"):
            return TruffleHogAdapter()

    def test_timeout_returns_empty_list(self, tmp_path):
        import subprocess

        adapter = self._make_adapter()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("trufflehog", 120)):
            findings = adapter.scan_directory(tmp_path)
        assert findings == []

    def test_os_error_returns_empty_list(self, tmp_path):
        adapter = self._make_adapter()
        with patch("subprocess.run", side_effect=OSError("exec failed")):
            findings = adapter.scan_directory(tmp_path)
        assert findings == []


# ── verified_only flag ────────────────────────────────────────────────────────


class TestTruffleHogVerifiedOnly:
    def test_verified_only_adds_flag_to_command(self, tmp_path):
        with patch("shutil.which", return_value="/usr/local/bin/trufflehog"):
            adapter = TruffleHogAdapter(verified_only=True)
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            adapter.scan_directory(tmp_path)
        cmd = mock_run.call_args[0][0]
        assert "--only-verified" in cmd

    def test_default_includes_unverified(self, tmp_path):
        with patch("shutil.which", return_value="/usr/local/bin/trufflehog"):
            adapter = TruffleHogAdapter(verified_only=False)
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            adapter.scan_directory(tmp_path)
        cmd = mock_run.call_args[0][0]
        assert "--only-verified" not in cmd
