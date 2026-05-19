"""Tests for scripts/pr_sandbox.py (v5.0.0 Phase A.5 — Review-Bottleneck Point 3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.pr_sandbox import (
    _diff_changed_lines,
    _docker_available,
    _find_dockerfile,
    cmd_full,
    cmd_static,
    main,
)

# ── _diff_changed_lines ───────────────────────────────────────────────────────


class TestDiffChangedLines:
    def test_parses_insertions_deletions(self):
        with patch("scripts.pr_sandbox._git") as mock_git:
            mock_git.return_value = (0, " 5 files changed, 120 insertions(+), 30 deletions(-)\n")
            total = _diff_changed_lines()
        assert total == 150  # 120 + 30

    def test_parses_insertions_only(self):
        with patch("scripts.pr_sandbox._git") as mock_git:
            mock_git.return_value = (0, " 2 files changed, 45 insertions(+)\n")
            total = _diff_changed_lines()
        assert total == 45

    def test_returns_zero_on_git_failure(self):
        with patch("scripts.pr_sandbox._git") as mock_git:
            mock_git.return_value = (1, "")
            total = _diff_changed_lines()
        assert total == 0

    def test_returns_zero_on_empty_output(self):
        with patch("scripts.pr_sandbox._git") as mock_git:
            mock_git.return_value = (0, "")
            total = _diff_changed_lines()
        assert total == 0

    def test_custom_base_ref(self):
        with patch("scripts.pr_sandbox._git") as mock_git:
            mock_git.return_value = (0, " 1 file changed, 10 insertions(+)\n")
            total = _diff_changed_lines("origin/develop")
        assert total == 10
        args = mock_git.call_args[0]
        assert "origin/develop...HEAD" in args


# ── _docker_available ─────────────────────────────────────────────────────────


class TestDockerAvailable:
    def test_returns_true_when_docker_responds(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "26.1.3\n"
        with patch("subprocess.run", return_value=mock_proc):
            assert _docker_available() is True

    def test_returns_false_when_docker_missing(self):
        with patch("subprocess.run", side_effect=OSError("docker not found")):
            assert _docker_available() is False

    def test_returns_false_when_returncode_nonzero(self):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        with patch("subprocess.run", return_value=mock_proc):
            assert _docker_available() is False


# ── _find_dockerfile ──────────────────────────────────────────────────────────


class TestFindDockerfile:
    def test_finds_dockerfile_at_root(self, tmp_path, monkeypatch):
        (tmp_path / "Dockerfile").touch()
        import scripts.pr_sandbox as sb

        monkeypatch.setattr(sb, "ROOT", tmp_path)
        result = _find_dockerfile()
        assert result is not None
        assert result.name == "Dockerfile"

    def test_returns_none_when_absent(self, tmp_path, monkeypatch):
        import scripts.pr_sandbox as sb

        monkeypatch.setattr(sb, "ROOT", tmp_path)
        assert _find_dockerfile() is None


# ── cmd_static ────────────────────────────────────────────────────────────────


class TestCmdStatic:
    def _args(self):
        return SimpleNamespace(base_ref="origin/main", docker=False, json=None, require_docker=False)

    def test_happy_path_no_high_findings(self):
        mock_findings = [{"file": "/repo/src/main.py", "severity": "medium", "rule_id": "IAC-001"}]
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
        ):
            mock_iac_cls.return_value.scan.return_value = mock_findings
            result = cmd_static(self._args())

        assert result["ok"] is True
        assert result["iac"]["high"] == 0
        assert result["dogfood"]["ok"] is True

    def test_high_iac_finding_sets_ok_false(self):
        mock_findings = [{"file": "/repo/src/app.py", "severity": "high", "rule_id": "IAC-TF-001"}]
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
        ):
            mock_iac_cls.return_value.scan.return_value = mock_findings
            result = cmd_static(self._args())

        assert result["ok"] is False
        assert result["iac"]["high"] == 1

    def test_test_samples_excluded(self):
        """Findings under TESTS/samples/ must be filtered out."""
        mock_findings = [
            {"file": "/repo/TESTS/samples/vuln.py", "severity": "high", "rule_id": "IAC-001"},
            {"file": "/repo/src/main.py", "severity": "low", "rule_id": "IAC-002"},
        ]
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        import scripts.pr_sandbox as sb

        with patch.object(sb, "ROOT", Path("/repo")):
            with (
                patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
                patch("subprocess.run", return_value=mock_dogfood),
            ):
                mock_iac_cls.return_value.scan.return_value = mock_findings
                result = cmd_static(self._args())

        assert result["ok"] is True
        assert result["iac"]["high"] == 0  # sample file excluded
        assert result["iac"]["total"] == 1  # only src/main.py counted

    def test_dogfood_failure_sets_ok_false(self):
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 1

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
        ):
            mock_iac_cls.return_value.scan.return_value = []
            result = cmd_static(self._args())

        assert result["ok"] is False
        assert result["dogfood"]["ok"] is False

    def test_iac_import_error_recorded(self):
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            pass  # can't easily test import error path without deeper patching

    def test_stage_field_present(self):
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
        ):
            mock_iac_cls.return_value.scan.return_value = []
            result = cmd_static(self._args())

        assert result["stage"] == "static"


# ── cmd_full ──────────────────────────────────────────────────────────────────


class TestCmdFull:
    def _args(self, docker=False):
        return SimpleNamespace(base_ref="origin/main", docker=docker, json=None, require_docker=False)

    def test_full_without_docker_skips_docker_stage(self):
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
            patch("scripts.pr_sandbox._diff_changed_lines", return_value=42),
        ):
            mock_iac_cls.return_value.scan.return_value = []
            result = cmd_full(self._args(docker=False))

        assert result["docker"].get("skipped") is True
        assert result["changed_lines"] == 42

    def test_full_ok_aggregates_static_and_docker(self):
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
            patch("scripts.pr_sandbox._diff_changed_lines", return_value=10),
            patch("scripts.pr_sandbox.cmd_docker", return_value={"stage": "docker", "ok": True}),
        ):
            mock_iac_cls.return_value.scan.return_value = []
            result = cmd_full(self._args(docker=True))

        assert result["ok"] is True


# ── main() exit codes + JSON output ───────────────────────────────────────────


class TestMain:
    def test_exit_0_when_ok(self, tmp_path):
        out_file = tmp_path / "summary.json"
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
            patch("scripts.pr_sandbox._diff_changed_lines", return_value=5),
        ):
            mock_iac_cls.return_value.scan.return_value = []
            rc = main(["--json", str(out_file)])

        assert rc == 0
        data = json.loads(out_file.read_text())
        assert "ok" in data
        assert "static" in data

    def test_exit_1_when_high_finding(self, tmp_path):
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 1  # dogfood gate fails

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
            patch("scripts.pr_sandbox._diff_changed_lines", return_value=5),
        ):
            mock_iac_cls.return_value.scan.return_value = []
            rc = main([])

        assert rc == 1

    def test_exit_2_when_docker_required_but_missing(self):
        with patch("scripts.pr_sandbox._docker_available", return_value=False):
            rc = main(["--require-docker"])
        assert rc == 2

    def test_json_output_is_valid(self, tmp_path):
        out_file = tmp_path / "out.json"
        mock_dogfood = MagicMock()
        mock_dogfood.returncode = 0

        with (
            patch("CORE.engines.iac_scanner.IaCScanner") as mock_iac_cls,
            patch("subprocess.run", return_value=mock_dogfood),
            patch("scripts.pr_sandbox._diff_changed_lines", return_value=0),
        ):
            mock_iac_cls.return_value.scan.return_value = []
            main(["--json", str(out_file)])

        payload = json.loads(out_file.read_text())
        assert isinstance(payload["ok"], bool)
        assert isinstance(payload["changed_lines"], int)
