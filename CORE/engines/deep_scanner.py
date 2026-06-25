"""Deep AST security scanner — product integration of the deterministic engine.

The shipping pipeline historically ran Ruff/Semgrep/Bandit/Vulture, which produce mostly
style/quality findings and very little real security recall (≈1 security finding on a repo where
real vulnerabilities number in the dozens). The project's deterministic AST engine
(`scripts/ast_security_scanner.py`) is what actually achieves the headline RealVuln recall, but
it lived only in the benchmark harness and was never wired into the product.

This module bridges that gap: it runs the AST engine and converts its findings into the
`CanonicalFinding`-compatible dicts the rest of the pipeline consumes, so the product genuinely
detects what the benchmark measures.

OPT-IN (ACRQA_DEEP_SCAN=1), off by default. It dramatically raises security recall, but the
downstream per-finding engines (taint / reachability / exploit-verification) were tuned for a
handful of security findings and do not yet scale to the dozens this produces — running them on
every recall-mode finding is slow. The proper fix is to run those expensive engines only on the
Confirmed (≥2-engine) tier; until then this stays opt-in. The engine output here is correct and
fast; the limitation is the pipeline that consumes it.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS = _ROOT / "scripts"

# CWE → severity for the families the AST engine emits. Injection / auth-bypass / deserialization
# are high; information-exposure / config / weak-crypto are medium; the rest default to medium.
_CWE_SEVERITY: dict[str, str] = {
    "CWE-89": "high",  # SQL injection
    "CWE-78": "high",  # command injection
    "CWE-94": "high",  # code injection
    "CWE-95": "high",
    "CWE-79": "high",  # XSS
    "CWE-80": "high",
    "CWE-22": "high",  # path traversal
    "CWE-918": "high",  # SSRF
    "CWE-502": "high",  # insecure deserialization
    "CWE-1336": "high",  # SSTI
    "CWE-306": "high",  # missing authentication
    "CWE-862": "high",  # missing authorization
    "CWE-639": "high",  # IDOR
    "CWE-287": "high",  # improper authentication
    "CWE-798": "high",  # hardcoded credentials
    "CWE-352": "medium",  # CSRF
    "CWE-307": "medium",  # no brute-force protection
    "CWE-601": "medium",  # open redirect
    "CWE-209": "medium",  # error info exposure
    "CWE-200": "medium",  # sensitive data exposure
    "CWE-215": "medium",  # debug mode
    "CWE-256": "medium",  # plaintext password storage
    "CWE-312": "medium",
    "CWE-327": "medium",  # weak crypto
    "CWE-328": "medium",
    "CWE-916": "medium",  # weak hash
    "CWE-330": "medium",  # insufficient randomness
    "CWE-338": "medium",
    "CWE-259": "medium",  # hardcoded password default
    "CWE-532": "low",  # log info exposure
    "CWE-1333": "medium",  # ReDoS
    "CWE-284": "medium",  # improper access control
    "CWE-614": "low",  # insecure cookie
    "CWE-1004": "low",  # httponly cookie
}


def run_deep_scan(target_dir: str) -> list[dict]:
    """Run the deterministic AST engine and return CanonicalFinding-compatible dicts.

    Returns [] (never raises) if the engine is unavailable or errors — additive by design, so a
    failure here must never break the main pipeline.
    """
    try:
        if str(_SCRIPTS) not in sys.path:
            sys.path.insert(0, str(_SCRIPTS))
        from ast_security_scanner import scan_repo as ast_scan
    except Exception as e:  # pragma: no cover - import guard
        logger.warning("deep_scanner: AST engine unavailable: %s", e)
        return []

    # Reuse the project's CWE → canonical SECURITY-* mapping so deep findings are recognised as
    # security by every downstream stage (gate, scoring, reporting) exactly like the LLM path.
    try:
        from CORE.engines.llm_detector import CANONICAL_CWE_MAP
    except Exception:  # pragma: no cover
        CANONICAL_CWE_MAP = {}

    try:
        raw = ast_scan(str(target_dir))
    except Exception as e:
        logger.warning("deep_scanner: scan failed: %s", e)
        return []

    out: list[dict] = []
    base = Path(target_dir)
    for f in raw:
        cwe = str(f.get("cwe", "")).strip()
        if not cwe:
            continue
        rel = str(f.get("file", ""))
        # AST engine returns repo-relative paths; make them absolute for downstream consistency.
        abs_path = str(base / rel) if not Path(rel).is_absolute() else rel
        out.append(
            {
                # Canonical SECURITY-* id so the gate/scoring/reporting count it as security; the
                # precise CWE is preserved in message + tool_raw for granular display.
                "canonical_rule_id": CANONICAL_CWE_MAP.get(cwe, "SECURITY-001"),
                "canonical_severity": _CWE_SEVERITY.get(cwe, "medium"),
                "severity": _CWE_SEVERITY.get(cwe, "medium"),
                "category": "security",
                "file": abs_path,
                "file_path": abs_path,
                "line": f.get("line", 0) or 0,
                "language": "python",
                "message": f.get("description") or f"{cwe} detected by deterministic AST engine",
                "tool_raw": {
                    "tool_name": "deep_ast_scanner",
                    "source": "deep-ast",
                    "cwe": cwe,
                    "original_output": dict(f),
                },
            }
        )
    return out
