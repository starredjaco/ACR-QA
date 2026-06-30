"""
Unit tests for the deep AST scanner (product integration of the deterministic engine).

These run the engine directly (not the full pipeline), so they are fast and cover the contract the
rest of CORE relies on: every finding is a security finding with a canonical SECURITY-* rule id, an
explicit severity, and the originating CWE preserved in tool_raw.
"""

from pathlib import Path

from CORE.engines.deep_scanner import run_deep_scan

_SAMPLE = str(Path(__file__).parent / "samples" / "comprehensive-issues")


class TestDeepScanner:
    """Contract + behavior of run_deep_scan()."""

    def test_finds_known_vulnerabilities(self):
        """The deterministic engine surfaces real vulns the legacy tool pass misses."""
        findings = run_deep_scan(_SAMPLE)
        assert len(findings) > 0, "expected security findings on the comprehensive-issues sample"

    def test_detects_sql_injection(self):
        """CWE-89 (SQL injection) is present — the sample's dominant vulnerability class."""
        findings = run_deep_scan(_SAMPLE)
        cwes = {(f.get("tool_raw") or {}).get("cwe") for f in findings}
        assert "CWE-89" in cwes, f"expected CWE-89 in {cwes}"

    def test_canonical_contract(self):
        """Every finding satisfies the CanonicalFinding-compatible contract CORE consumes."""
        findings = run_deep_scan(_SAMPLE)
        assert findings
        for f in findings:
            assert f["category"] == "security"
            assert str(f["canonical_rule_id"]).startswith("SECURITY-")
            assert f["canonical_severity"] in {"high", "medium", "low"}
            assert f["severity"] in {"high", "medium", "low"}
            assert f.get("file") and f.get("line") is not None
            assert f.get("message")
            tr = f.get("tool_raw") or {}
            assert tr.get("source") == "deep-ast"
            assert str(tr.get("cwe", "")).startswith("CWE-")

    def test_deterministic(self):
        """Same input → identical findings (the engine's core guarantee)."""
        a = run_deep_scan(_SAMPLE)
        b = run_deep_scan(_SAMPLE)
        key = lambda fs: sorted((f["canonical_rule_id"], f["file"], f["line"]) for f in fs)  # noqa: E731
        assert key(a) == key(b)

    def test_graceful_on_missing_path(self):
        """A nonexistent target never raises — additive by design, must not break the pipeline."""
        assert run_deep_scan("/nonexistent/path/xyz") == []
