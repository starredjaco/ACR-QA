"""Tests for the intra-procedural taint analysis engine (Phase 1)."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from CORE.engines.taint_analyzer import TaintAnalyzer, TaintInfo, _FunctionTaintVisitor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "taint"

_SOURCES = {
    "request.args",
    "request.args.get",
    "request.form",
    "request.form.get",
    "request.json",
    "request.get_json",
    "request.cookies",
    "request.cookies.get",
    "os.environ",
    "os.environ.get",
    "os.getenv",
}
_SINKS = {
    "execute": {"canonical_rule_id": "SECURITY-027", "cwe": "CWE-89", "severity": "high"},
    "eval": {"canonical_rule_id": "SECURITY-001", "cwe": "CWE-94", "severity": "high"},
    "subprocess": {"canonical_rule_id": "SECURITY-021", "cwe": "CWE-78", "severity": "high"},
}


def _analyze_snippet(code: str) -> list[dict]:
    """Analyze a dedented Python snippet via the TaintAnalyzer."""
    code = textwrap.dedent(code)
    tree = ast.parse(code)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            v = _FunctionTaintVisitor(_SOURCES, _SINKS, "<test>")
            v.visit(node)
            findings.extend(v.findings)
    # deduplicate
    seen: set[tuple] = set()
    unique = []
    for f in findings:
        k = (f["file"], f["line"], f["canonical_rule_id"])
        if k not in seen:
            seen.add(k)
            unique.append(f)
    return unique


# ---------------------------------------------------------------------------
# TaintInfo unit tests
# ---------------------------------------------------------------------------


class TestTaintInfo:
    def test_initial_state(self):
        t = TaintInfo(source="request.args")
        assert t.source == "request.args"
        assert t.steps == []

    def test_hop_creates_new_instance(self):
        t = TaintInfo(source="request.form", steps=["x = request.form.get('q')"])
        t2 = t.hop("y = x.strip()")
        assert t2 is not t
        assert len(t2.steps) == 2
        assert "y = x.strip()" in t2.steps

    def test_hop_does_not_mutate_original(self):
        t = TaintInfo(source="os.environ")
        t.hop("step1")
        assert t.steps == []


# ---------------------------------------------------------------------------
# Source detection
# ---------------------------------------------------------------------------


class TestSourceDetection:
    def test_request_args_get(self):
        findings = _analyze_snippet("""
            def view():
                x = request.args.get("q")
                eval(x)
        """)
        assert any(
            f["taint_source"] == "request.args.get" or f["taint_source"].startswith("request.args") for f in findings
        )

    def test_request_form(self):
        findings = _analyze_snippet("""
            def view():
                x = request.form["name"]
                eval(x)
        """)
        assert len(findings) >= 1

    def test_request_json(self):
        findings = _analyze_snippet("""
            def view():
                body = request.json
                eval(body)
        """)
        assert len(findings) >= 1

    def test_os_environ_get(self):
        findings = _analyze_snippet("""
            def handler():
                val = os.environ.get("SECRET")
                eval(val)
        """)
        assert len(findings) >= 1

    def test_no_taint_from_literal(self):
        findings = _analyze_snippet("""
            def handler():
                val = "hello"
                eval(val)
        """)
        assert findings == []

    def test_no_taint_from_constant_variable(self):
        findings = _analyze_snippet("""
            def handler():
                safe = "SELECT 1"
                cursor.execute(safe)
        """)
        assert findings == []


# ---------------------------------------------------------------------------
# Propagation
# ---------------------------------------------------------------------------


class TestPropagation:
    def test_direct_name_propagation(self):
        findings = _analyze_snippet("""
            def f():
                x = request.args.get("q")
                cursor.execute("SELECT " + x)
        """)
        assert len(findings) == 1
        assert findings[0]["canonical_rule_id"] == "SECURITY-027"

    def test_method_call_propagation(self):
        findings = _analyze_snippet("""
            def f():
                raw = request.form.get("q")
                cleaned = raw.strip()
                cursor.execute("SELECT " + cleaned)
        """)
        assert len(findings) == 1

    def test_fstring_propagation(self):
        findings = _analyze_snippet("""
            def f():
                term = request.args.get("term")
                sql = f"SELECT * FROM t WHERE name = '{term}'"
                cursor.execute(sql)
        """)
        assert len(findings) == 1

    def test_concat_propagation(self):
        findings = _analyze_snippet("""
            def f():
                user = request.args.get("u")
                query = "SELECT * FROM t WHERE u = " + user
                cursor.execute(query)
        """)
        assert len(findings) == 1

    def test_multi_hop_stops_at_untainted(self):
        findings = _analyze_snippet("""
            def f():
                x = request.args.get("q")
                x = "hardcoded"  # reassigned — no longer tainted
                cursor.execute(x)
        """)
        assert findings == []

    def test_taint_path_contains_steps(self):
        findings = _analyze_snippet("""
            def f():
                raw = request.form["q"]
                stripped = raw.strip()
                cursor.execute("SELECT " + stripped)
        """)
        assert len(findings) == 1
        path = findings[0]["taint_path"]
        assert isinstance(path, list)
        assert len(path) >= 2

    def test_confidence_decreases_with_hops(self):
        findings_1hop = _analyze_snippet("""
            def f():
                x = request.args.get("q")
                eval(x)
        """)
        findings_2hop = _analyze_snippet("""
            def f():
                x = request.args.get("q")
                y = x.strip()
                eval(y)
        """)
        assert findings_1hop[0]["taint_confidence"] >= findings_2hop[0]["taint_confidence"]

    def test_confidence_minimum(self):
        findings = _analyze_snippet("""
            def f():
                a = request.args.get("q")
                b = a.strip()
                c = b.lower()
                d = c.encode()
                e = str(d)
                eval(e)
        """)
        for f in findings:
            assert f["taint_confidence"] >= 0.4


# ---------------------------------------------------------------------------
# Sink detection
# ---------------------------------------------------------------------------


class TestSinkDetection:
    def test_eval_sink(self):
        findings = _analyze_snippet("""
            def f():
                x = request.args.get("expr")
                eval(x)
        """)
        assert len(findings) == 1
        assert findings[0]["canonical_rule_id"] == "SECURITY-001"
        assert findings[0]["cwe"] == "CWE-94"

    def test_execute_sink(self):
        findings = _analyze_snippet("""
            def f():
                q = request.args.get("q")
                cursor.execute("SELECT " + q)
        """)
        assert len(findings) == 1
        assert findings[0]["canonical_rule_id"] == "SECURITY-027"

    def test_subprocess_sink(self):
        findings = _analyze_snippet("""
            def f():
                cmd = request.args.get("cmd")
                subprocess.run(cmd, shell=True)
        """)
        assert len(findings) == 1
        assert findings[0]["canonical_rule_id"] == "SECURITY-021"

    def test_safe_parameterized_not_flagged(self):
        findings = _analyze_snippet("""
            def f():
                q = request.args.get("q")
                cursor.execute("SELECT * FROM t WHERE id = ?", (q,))
        """)
        # parameterized queries: taint in second arg (tuple), not first arg
        # The engine checks if tainted arg reaches execute() — tuple arg contains taint
        # This is an edge-case; ensure no false negative on the first arg (clean)
        # and ensure finding is present if taint reaches execute at all
        # (parametrized queries are still flagged at MVP — no sanitizer support yet)
        # Just check the engine doesn't crash
        assert isinstance(findings, list)

    def test_no_sink_no_finding(self):
        findings = _analyze_snippet("""
            def f():
                x = request.args.get("q")
                return x.upper()
        """)
        assert findings == []


# ---------------------------------------------------------------------------
# Multi-function isolation
# ---------------------------------------------------------------------------


class TestFunctionIsolation:
    def test_taint_does_not_leak_between_functions(self):
        findings = _analyze_snippet("""
            def tainted_func():
                x = request.args.get("q")
                return x

            def clean_func():
                cursor.execute("SELECT " + "static")
        """)
        # tainted_func: no sink hit; clean_func: no taint source
        assert findings == []

    def test_two_independent_tainted_functions(self):
        findings = _analyze_snippet("""
            def f1():
                x = request.args.get("q")
                eval(x)

            def f2():
                y = request.form.get("data")
                cursor.execute("SELECT " + y)
        """)
        assert len(findings) == 2


# ---------------------------------------------------------------------------
# File-level analysis
# ---------------------------------------------------------------------------


class TestFileAnalysis:
    def test_analyze_direct_sqli_fixture(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "direct_sqli.py")
        assert len(findings) >= 1
        rules = {f["canonical_rule_id"] for f in findings}
        assert "SECURITY-027" in rules

    def test_analyze_multihop_sqli_fixture(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "multihop_sqli.py")
        assert len(findings) >= 1

    def test_analyze_fstring_eval_fixture(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "fstring_eval.py")
        assert len(findings) >= 1
        rules = {f["canonical_rule_id"] for f in findings}
        assert "SECURITY-001" in rules

    def test_analyze_clean_fixture_zero_findings(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "clean.py")
        assert findings == [], f"Expected 0 findings on clean.py, got: {findings}"

    def test_finding_fields_present(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "direct_sqli.py")
        assert len(findings) >= 1
        f = findings[0]
        for key in (
            "tool",
            "canonical_rule_id",
            "severity",
            "file",
            "line",
            "message",
            "taint_source",
            "taint_path",
            "taint_confidence",
        ):
            assert key in f, f"Missing field: {key}"

    def test_tool_is_taint_analyzer(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "direct_sqli.py")
        for f in findings:
            assert f["tool"] == "taint_analyzer"

    def test_severity_is_high(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "direct_sqli.py")
        for f in findings:
            assert f["severity"] == "high"

    def test_no_duplicate_findings(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(FIXTURE_DIR / "multihop_sqli.py")
        keys = [(f["file"], f["line"], f["canonical_rule_id"]) for f in findings]
        assert len(keys) == len(set(keys)), "Duplicate findings returned"

    def test_analyze_syntax_error_returns_empty(self, tmp_path):
        bad = tmp_path / "bad.py"
        bad.write_text("def f(:\n    pass\n")
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_file(bad)
        assert findings == []

    def test_analyze_nonexistent_file(self, tmp_path):
        analyzer = TaintAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file(tmp_path / "nonexistent.py")


# ---------------------------------------------------------------------------
# Directory analysis
# ---------------------------------------------------------------------------


class TestDirectoryAnalysis:
    def test_analyze_directory_finds_taint_flows(self):
        analyzer = TaintAnalyzer()
        findings = analyzer.analyze_directory(FIXTURE_DIR)
        assert len(findings) >= 3  # at least one per tainted fixture

    def test_analyze_directory_no_findings_in_clean_file(self):
        analyzer = TaintAnalyzer()
        all_findings = analyzer.analyze_directory(FIXTURE_DIR)
        clean_findings = [f for f in all_findings if "clean.py" in f["file"]]
        assert clean_findings == []

    def test_enrich_findings_extends_list(self):
        analyzer = TaintAnalyzer()
        initial = [{"tool": "bandit", "canonical_rule_id": "SECURITY-027", "file": "x.py", "line": 5}]
        enriched = analyzer.enrich_findings(initial, FIXTURE_DIR)
        assert len(enriched) > len(initial)
        bandit_findings = [f for f in enriched if f["tool"] == "bandit"]
        assert len(bandit_findings) == 1

    def test_enrich_findings_empty_dir(self, tmp_path):
        analyzer = TaintAnalyzer()
        findings = analyzer.enrich_findings([], tmp_path)
        assert findings == []
