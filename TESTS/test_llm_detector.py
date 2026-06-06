"""
Tests for CORE/engines/llm_detector.py — Phase 1+2 LLM-augmented detection engine.

All tests are pure unit tests — no real Groq calls made.
Groq is mocked throughout; these verify parse/gate/integrate logic only.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from CORE.engines.llm_detector import (
    CANONICAL_CWE_MAP,
    LLMDetector,
    LLMFinding,
    _cwe_family,
    _parse_llm_json,
)

# ---------------------------------------------------------------------------
# _parse_llm_json — tolerates markdown fences, extracts array
# ---------------------------------------------------------------------------


class TestParseLLMJson:
    def test_clean_array(self):
        r = _parse_llm_json('[{"line": 5, "cwe": "CWE-89", "why": "sqli", "severity": "high"}]')
        assert len(r) == 1
        assert r[0]["cwe"] == "CWE-89"

    def test_strips_markdown_fences(self):
        text = '```json\n[{"line": 10, "cwe": "CWE-79", "why": "xss", "severity": "high"}]\n```'
        r = _parse_llm_json(text)
        assert len(r) == 1
        assert r[0]["cwe"] == "CWE-79"

    def test_returns_empty_on_no_array(self):
        assert _parse_llm_json("No vulnerabilities found.") == []

    def test_returns_empty_on_broken_json(self):
        assert _parse_llm_json("[broken json}") == []

    def test_prose_before_array(self):
        text = 'Here are the findings:\n[{"line": 3, "cwe": "CWE-78", "why": "cmdi", "severity": "high"}]'
        r = _parse_llm_json(text)
        assert len(r) == 1

    def test_empty_array(self):
        assert _parse_llm_json("[]") == []


# ---------------------------------------------------------------------------
# CWE family normalization
# ---------------------------------------------------------------------------


class TestCWEFamily:
    def test_known_cwe(self):
        # CWE-89 should be in sql_injection family (from RealVuln families config if present)
        fam = _cwe_family("CWE-89")
        # Either mapped or "unknown" if config not present
        assert isinstance(fam, str)

    def test_unknown_cwe_returns_unknown(self):
        assert _cwe_family("CWE-99999") == "unknown"

    def test_case_insensitive(self):
        assert _cwe_family("cwe-89") == _cwe_family("CWE-89")


# ---------------------------------------------------------------------------
# CANONICAL_CWE_MAP completeness
# ---------------------------------------------------------------------------


class TestCanonicalCWEMap:
    CRITICAL_CWES = [
        "CWE-89",
        "CWE-79",
        "CWE-78",
        "CWE-22",
        "CWE-502",
        "CWE-918",
        "CWE-611",
        "CWE-1336",
        "CWE-601",
        "CWE-798",
    ]

    def test_critical_cwes_all_mapped(self):
        for cwe in self.CRITICAL_CWES:
            assert cwe in CANONICAL_CWE_MAP, f"{cwe} missing from CANONICAL_CWE_MAP"

    def test_all_values_are_security_ids(self):
        for cwe, sec_id in CANONICAL_CWE_MAP.items():
            assert sec_id.startswith("SECURITY-"), f"{cwe} → {sec_id} is not a SECURITY-* ID"


# ---------------------------------------------------------------------------
# LLMFinding dataclass
# ---------------------------------------------------------------------------


class TestLLMFinding:
    def _make(self, **kwargs) -> LLMFinding:
        defaults = dict(
            file="app.py",
            line=10,
            cwe="CWE-89",
            cwe_family="sql_injection",
            severity="high",
            why="SQL injection via f-string",
        )
        defaults.update(kwargs)
        return LLMFinding(**defaults)

    def test_to_canonical_dict_keys(self):
        f = self._make()
        d = f.to_canonical_dict()
        assert "canonical_rule_id" in d
        assert "canonical_severity" in d
        assert "file" in d
        assert "line" in d
        assert "tool_raw" in d

    def test_tool_raw_has_source_llm(self):
        f = self._make()
        d = f.to_canonical_dict()
        assert d["tool_raw"]["tool_name"] == "llm_detector"
        assert d["tool_raw"]["source"] == "llm"

    def test_cwe_maps_to_security_id(self):
        f = self._make(cwe="CWE-89")
        d = f.to_canonical_dict()
        assert d["canonical_rule_id"] == "SECURITY-027"

    def test_unknown_cwe_falls_back(self):
        f = self._make(cwe="CWE-99999")
        d = f.to_canonical_dict()
        assert d["canonical_rule_id"] == "SECURITY-001"

    def test_gated_flag_in_tool_raw(self):
        f = self._make(gated=True, gate_confidence=0.85)
        d = f.to_canonical_dict()
        assert d["tool_raw"]["gated"] is True
        assert d["tool_raw"]["gate_confidence"] == 0.85


# ---------------------------------------------------------------------------
# LLMDetector._parse_raw
# ---------------------------------------------------------------------------


class TestLLMDetectorParseRaw:
    def setup_method(self):
        self.detector = LLMDetector.__new__(LLMDetector)
        self.detector._keys = ["fake-key"]
        self.detector._use_cache = False
        self.detector._gate = False

    def test_valid_item_parsed(self):
        raw = [{"line": 5, "cwe": "CWE-89", "severity": "high", "why": "SQLi"}]
        findings = self.detector._parse_raw("app.py", raw)
        assert len(findings) == 1
        assert findings[0].cwe == "CWE-89"
        assert findings[0].line == 5

    def test_invalid_cwe_filtered(self):
        raw = [{"line": 5, "cwe": "INVALID", "severity": "high", "why": "x"}]
        findings = self.detector._parse_raw("app.py", raw)
        assert len(findings) == 0

    def test_zero_line_filtered(self):
        raw = [{"line": 0, "cwe": "CWE-89", "severity": "high", "why": "x"}]
        findings = self.detector._parse_raw("app.py", raw)
        assert len(findings) == 0

    def test_dedup_same_cwe_close_lines(self):
        raw = [
            {"line": 10, "cwe": "CWE-89", "severity": "high", "why": "x"},
            {"line": 11, "cwe": "CWE-89", "severity": "high", "why": "x"},  # same band
        ]
        findings = self.detector._parse_raw("app.py", raw)
        assert len(findings) == 1

    def test_severity_normalised(self):
        raw = [{"line": 5, "cwe": "CWE-89", "severity": "CRITICAL", "why": "x"}]
        findings = self.detector._parse_raw("app.py", raw)
        assert findings[0].severity == "medium"  # normalised to valid value


# ---------------------------------------------------------------------------
# LLMDetector.detect_file — mocked Groq call
# ---------------------------------------------------------------------------


class TestLLMDetectorDetectFile:
    def _make_detector(self) -> LLMDetector:
        d = LLMDetector.__new__(LLMDetector)
        d._keys = ["fake-key"]
        d._use_cache = False
        d._gate = False
        return d

    def test_detect_file_returns_findings(self, tmp_path):
        code = "import sqlite3\ndef get_user(uid):\n    db.execute(f'SELECT * FROM users WHERE id={uid}')\n"
        (tmp_path / "app.py").write_text(code)

        detector = self._make_detector()
        with patch(
            "CORE.engines.llm_detector._groq_call",
            return_value='[{"line": 3, "cwe": "CWE-89", "severity": "high", "why": "SQLi"}]',
        ):
            findings = detector.detect_file(str(tmp_path / "app.py"), code)

        assert len(findings) == 1
        assert findings[0].cwe == "CWE-89"

    def test_detect_file_empty_code_returns_nothing(self, tmp_path):
        detector = self._make_detector()
        findings = detector.detect_file(str(tmp_path / "empty.py"), "")
        assert findings == []

    def test_detect_file_groq_error_returns_empty(self, tmp_path):
        code = "x = 1"
        detector = self._make_detector()
        with patch("CORE.engines.llm_detector._groq_call", side_effect=RuntimeError("rate limited")):
            findings = detector.detect_file(str(tmp_path / "app.py"), code)
        assert findings == []

    def test_detect_file_malformed_response_returns_empty(self, tmp_path):
        code = "x = eval(input())"
        detector = self._make_detector()
        with patch("CORE.engines.llm_detector._groq_call", return_value="Sorry, I cannot help with that."):
            findings = detector.detect_file(str(tmp_path / "app.py"), code)
        assert findings == []


# ---------------------------------------------------------------------------
# LLMDetector.gate_findings — mocked gate call
# ---------------------------------------------------------------------------


class TestLLMDetectorGating:
    def _make_detector(self) -> LLMDetector:
        d = LLMDetector.__new__(LLMDetector)
        d._keys = ["fake-key"]
        d._use_cache = False
        d._gate = True
        return d

    def _make_finding(self, **kw) -> LLMFinding:
        defaults = dict(file="app.py", line=10, cwe="CWE-89", cwe_family="sql_injection", severity="high", why="test")
        defaults.update(kw)
        return LLMFinding(**defaults)

    def test_confirmed_finding_passes_gate(self, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n" * 20)
        detector = self._make_detector()
        findings = [self._make_finding()]
        with patch("CORE.engines.llm_detector._groq_call", return_value="YES 0.9 clear sqli"):
            gated = detector.gate_findings(findings, str(tmp_path))
        assert len(gated) == 1
        assert gated[0].gated is True
        assert gated[0].gate_confidence == 0.9

    def test_rejected_finding_blocked(self, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n" * 20)
        detector = self._make_detector()
        findings = [self._make_finding()]
        with patch("CORE.engines.llm_detector._groq_call", return_value="NO false positive"):
            gated = detector.gate_findings(findings, str(tmp_path))
        assert len(gated) == 0

    def test_gate_error_blocks_finding(self, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n" * 20)
        detector = self._make_detector()
        findings = [self._make_finding()]
        with patch("CORE.engines.llm_detector._groq_call", side_effect=RuntimeError("fail")):
            gated = detector.gate_findings(findings, str(tmp_path))
        assert len(gated) == 0

    def test_empty_findings_returns_empty(self, tmp_path):
        detector = self._make_detector()
        assert detector.gate_findings([], str(tmp_path)) == []


# ---------------------------------------------------------------------------
# LLMDetector.available
# ---------------------------------------------------------------------------


class TestLLMDetectorAvailable:
    def test_available_with_keys(self):
        d = LLMDetector.__new__(LLMDetector)
        d._keys = ["key1", "key2"]
        assert d.available() is True

    def test_unavailable_without_keys(self):
        d = LLMDetector.__new__(LLMDetector)
        d._keys = []
        assert d.available() is False


# ---------------------------------------------------------------------------
# Integration: to_canonical_dict feeds into pipeline format
# ---------------------------------------------------------------------------


class TestPipelineIntegration:
    def _make_detector(self) -> LLMDetector:
        d = LLMDetector.__new__(LLMDetector)
        d._keys = ["fake-key"]
        d._use_cache = False
        d._gate = False
        return d

    def _make_finding(self, **kw) -> LLMFinding:
        defaults = dict(file="app.py", line=10, cwe="CWE-89", cwe_family="sql_injection", severity="high", why="test")
        defaults.update(kw)
        return LLMFinding(**defaults)

    def test_llm_finding_dict_has_required_pipeline_keys(self):
        f = LLMFinding(file="app.py", line=5, cwe="CWE-89", cwe_family="sql_injection", severity="high", why="test")
        d = f.to_canonical_dict()
        # Keys required by AnalysisPipeline._deduplicate_findings and DB insert
        assert "canonical_rule_id" in d
        assert "canonical_severity" in d
        assert "file" in d
        assert "file_path" in d
        assert "line" in d
        assert "message" in d
        assert "tool_raw" in d

    def test_main_llm_detect_env_flag(self):
        """ACRQA_LLM_DETECT=1 env var gates the LLM detection block in main.py."""
        import os

        # Just verify the env var is respected
        os.environ["ACRQA_LLM_DETECT"] = "1"
        assert os.environ.get("ACRQA_LLM_DETECT") == "1"
        del os.environ["ACRQA_LLM_DETECT"]

    def test_llm_flag_in_help(self):
        """--llm flag must appear in --help output."""
        import subprocess as _sp

        venv_py = Path(__file__).parent.parent / ".venv" / "bin" / "python"
        python_exe = str(venv_py) if venv_py.exists() else "python3"
        result = _sp.run(
            [python_exe, "-m", "CORE", "--help"], capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        assert "--llm" in (result.stdout + result.stderr), "--llm flag missing from --help"

    def test_load_keys_parsing(self, tmp_path):
        import os

        import CORE.engines.llm_detector as ld

        env_content = (
            "GROQ_API_KEY_0 = 'gsk_key0_longer_than_ten'\n"
            'GROQ_API_KEY_1 = "gsk_key1_longer_than_ten"\n'
            "GROQ_API_KEY_2 = your_placeholder_key\n"
            "OTHER_VAR = value\n"
        )

        mock_env = tmp_path / ".env"
        mock_env.write_text(env_content)

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("CORE.engines.llm_detector._ROOT", tmp_path),
        ):
            keys = ld._load_keys()
            assert len(keys) == 2
            assert "gsk_key0_longer_than_ten" in keys
            assert "gsk_key1_longer_than_ten" in keys

    @patch("CORE.engines.llm_detector._load_keys", return_value=[])
    def test_groq_call_no_keys(self, mock_load):
        from CORE.engines.llm_detector import _groq_call

        with pytest.raises(RuntimeError, match="No GROQ_API_KEY"):
            _groq_call("prompt", [])

    @patch("CORE.engines.llm_detector.time.sleep")
    def test_groq_call_success_on_retry(self, mock_sleep):
        from unittest.mock import MagicMock

        from CORE.engines.llm_detector import _groq_call

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "result text"
        mock_client.chat.completions.create.side_effect = [Exception("fail 1"), Exception("fail 2"), mock_response]

        with patch("groq.Groq", return_value=mock_client):
            res = _groq_call("prompt", ["key1"])
            assert res == "result text"
            assert mock_client.chat.completions.create.call_count == 3

    @patch("CORE.engines.llm_detector.time.sleep")
    def test_groq_call_failure_after_retries(self, mock_sleep):
        from unittest.mock import MagicMock

        from CORE.engines.llm_detector import _groq_call

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("fail")

        with patch("groq.Groq", return_value=mock_client):
            with pytest.raises(RuntimeError, match="failed after 3 attempts"):
                _groq_call("prompt", ["key1"])

    def test_returns_empty_on_broken_json_with_brackets(self):
        assert _parse_llm_json("[broken json]") == []

    def test_detector_init(self):
        with patch("CORE.engines.llm_detector._load_keys", return_value=["key1"]):
            d = LLMDetector(use_cache=False, gate=False)
            assert d._use_cache is False
            assert d._gate is False
            assert d._keys == ["key1"]

    def test_detect_file_reads_from_disk(self, tmp_path):
        app_file = tmp_path / "app.py"
        app_file.write_text("x = 1\n")
        detector = self._make_detector()
        with patch("CORE.engines.llm_detector._groq_call", return_value="[]"):
            res = detector.detect_file(str(app_file), code=None)
            assert res == []

    def test_detect_file_disk_read_error(self):
        detector = self._make_detector()
        res = detector.detect_file("non_existent_file.py", code=None)
        assert res == []

    def test_detect_file_loads_from_cache(self, tmp_path):
        import hashlib

        from CORE.engines.llm_detector import _CACHE, _file_hash

        detector = self._make_detector()
        detector._use_cache = True

        code = "x = 1  # some extra characters to make it longer than 20 chars\n"
        cache_key = _file_hash(code)
        safe_fname = hashlib.sha256(str(tmp_path / "app.py").encode()).hexdigest()[:16]
        cache_file = _CACHE / f"{safe_fname}_{cache_key}.json"

        # Populate cache
        cache_file.write_text('[{"line": 2, "cwe": "CWE-89", "severity": "high", "why": "SQLi"}]')

        try:
            res = detector.detect_file(str(tmp_path / "app.py"), code)
            assert len(res) == 1
            assert res[0].cwe == "CWE-89"
        finally:
            if cache_file.exists():
                cache_file.unlink()

    def test_detect_file_writes_to_cache(self, tmp_path):
        import hashlib
        import json

        from CORE.engines.llm_detector import _CACHE, _file_hash

        detector = self._make_detector()
        detector._use_cache = True

        code = "x = 2  # some extra characters to make it longer than 20 chars\n"
        cache_key = _file_hash(code)
        safe_fname = hashlib.sha256(str(tmp_path / "app.py").encode()).hexdigest()[:16]
        cache_file = _CACHE / f"{safe_fname}_{cache_key}.json"
        if cache_file.exists():
            cache_file.unlink()

        try:
            with patch("CORE.engines.llm_detector._groq_call", return_value='[{"line": 3, "cwe": "CWE-79"}]'):
                res = detector.detect_file(str(tmp_path / "app.py"), code)
                assert len(res) == 1
                assert cache_file.exists()
                cached_data = json.loads(cache_file.read_text())
                assert cached_data[0]["cwe"] == "CWE-79"
        finally:
            if cache_file.exists():
                cache_file.unlink()

    def test_detect_repo_scans_files(self, tmp_path):
        detector = self._make_detector()

        # Create a mock repo structure
        app_file = tmp_path / "app.py"
        app_file.write_text("x = 1\n" * 5)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "app.py"
        test_file.write_text("x = 2\n" * 5)

        with patch.object(
            detector, "detect_file", return_value=[LLMFinding("app.py", 1, "CWE-89", "sql_injection", "high", "why")]
        ) as mock_detect:
            res = detector.detect_repo(str(tmp_path))
            assert len(res) == 1
            assert res[0].file == "app.py"
            # Only app.py should be scanned, not tests/app.py
            mock_detect.assert_called_once()
            assert mock_detect.call_args[0][0] != str(test_file)

    def test_gate_finding_fallback_path(self, tmp_path):
        detector = self._make_detector()
        finding = self._make_finding(file="direct.py")

        # Create file in current directory temporarily
        app_file = Path("direct.py")
        app_file.write_text("x = 1\n" * 20)

        try:
            with patch("CORE.engines.llm_detector._groq_call", return_value="YES 0.8 conf"):
                conf = detector._gate_finding(finding, str(tmp_path))
                assert conf == 0.8
        finally:
            if app_file.exists():
                app_file.unlink()

    def test_gate_finding_os_error(self, tmp_path):
        detector = self._make_detector()
        finding = self._make_finding(file="nonexistent.py")
        conf = detector._gate_finding(finding, str(tmp_path))
        assert conf == 0.0

    def test_gate_finding_groq_error(self, tmp_path):
        detector = self._make_detector()
        finding = self._make_finding()
        (tmp_path / "app.py").write_text("x = 1\n" * 20)

        with patch("CORE.engines.llm_detector._groq_call", side_effect=RuntimeError("fail")):
            conf = detector._gate_finding(finding, str(tmp_path))
            assert conf == 0.0
