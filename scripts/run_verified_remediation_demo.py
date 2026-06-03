#!/usr/bin/env python3
"""
ACR-QA Verified Remediation Demo (Track C — v8 God Mode Plan, Pillar P1).

Demonstrates the frontier: detect → exploit-fires → AI fix → re-run same exploit
→ confirm it now fails → sign (vuln_proof, fix_diff, fix_proof) as one ECDSA bundle.

This is the one-command defense demo:
    python3 scripts/run_verified_remediation_demo.py

Exits 0 if ≥1 vuln class achieves fix_verified=True.
Exits 1 if Docker unavailable or all cases fail.

Scenarios (run in order):
  1. SQLi  — f-string query → parameterized
  2. CMDi  — shell=True → subprocess list
  3. SSTI  — render_template_string(user_input) → Markup.escape first
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from CORE.engines.verified_remediation import RemediationResult, VerifiedRemediationEngine

_ROOT = Path(__file__).parent.parent
_FIXTURES = _ROOT / "TESTS" / "fixtures" / "exploits"


def _banner(text: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {text}")
    print(f"{'=' * 65}")


def _scenario(name: str, fixture: str, finding_override: dict) -> RemediationResult | None:
    fixtures_dir = _FIXTURES / fixture
    if not fixtures_dir.exists():
        print(f"  ⚠  Fixture not found: {fixtures_dir}")
        return None

    app_file = fixtures_dir / "app.py"
    finding = {
        "id": f"demo-{fixture}",
        "canonical_severity": "high",
        "file": str(app_file),
        "file_path": str(app_file),
        "tool_raw": {
            "tool_name": "bandit",
            "original_output": {"issue_confidence": "HIGH"},
        },
        **finding_override,
    }

    engine = VerifiedRemediationEngine(use_docker=True, sign=True)
    print(f"\n  Running {name} scenario...")
    result = engine.run(finding, str(fixtures_dir))
    print(f"  {result.summary_line()}")

    if result.fix_diff:
        # Print first 20 diff lines
        diff_lines = result.fix_diff.splitlines()[:20]
        print("\n  Patch applied:")
        for ln in diff_lines:
            prefix = "  "
            if ln.startswith("+"):
                prefix = "\033[32m  "  # green
            elif ln.startswith("-"):
                prefix = "\033[31m  "  # red
            print(f"{prefix}{ln}\033[0m")

    if result.attestation:
        has_sig = bool(result.attestation.get("signature") or result.attestation.get("signed"))
        print(f"\n  Attestation: {'✅ signed' if has_sig else '⚠ unsigned bundle'}")

    return result


def main() -> None:
    _banner("ACR-QA Verified Remediation Demo")
    print(
        "\n  The frontier: detect → exploit-fires → AI fix → re-run same exploit\n"
        "  → confirm it now fails → sign (vuln_proof, fix_diff, fix_proof).\n"
        "  Snyk retests with a static engine. We retest with the live exploit.\n"
    )

    engine_check = VerifiedRemediationEngine(use_docker=True, sign=False)
    if not engine_check._verifier.is_docker_available():
        print("ERROR: Docker not available. Run with Docker daemon running.")
        sys.exit(1)

    scenarios = [
        (
            "SQL Injection",
            "flask_sqli",
            {
                "canonical_rule_id": "SECURITY-027",
                "line": 20,
                "message": "SQL injection via f-string formatting",
            },
        ),
        (
            "Command Injection",
            "flask_cmdi",
            {
                "canonical_rule_id": "SECURITY-021",
                "line": 15,
                "message": "Command injection via shell=True",
            },
        ),
        (
            "Server-Side Template Injection",
            "flask_ssti",
            {
                "canonical_rule_id": "SECURITY-031",
                "line": 10,
                "message": "SSTI in render_template_string with user input",
            },
        ),
    ]

    results = []
    for name, fixture, overrides in scenarios:
        _banner(f"Scenario: {name}")
        result = _scenario(name, fixture, overrides)
        if result:
            results.append((name, result))

    _banner("Summary")
    verified = [(n, r) for n, r in results if r.fix_verified]
    not_verified = [(n, r) for n, r in results if not r.fix_verified]

    print(f"\n  ✅ Fix verified ({len(verified)}/{len(results)}):")
    for name, r in verified:
        print(f"     {name} — {r.canonical_rule_id} — {r.duration_seconds:.1f}s")

    if not_verified:
        print(f"\n  ❌ Not verified ({len(not_verified)}/{len(results)}):")
        for name, r in not_verified:
            print(f"     {name} — {r.error or 'see above'}")

    if verified:
        print("\n  ✅ Verified Remediation: DEMONSTRATED")
        print("  The exploit was proven to fire, a patch was applied, and the")
        print("  same exploit was proven to fail — all signed to Rekor.")
        sys.exit(0)
    else:
        print("\n  ⚠  No scenario achieved fix_verified=True in this run.")
        print("  This is expected if Docker sandbox timing or LLM patch quality varies.")
        print("  Run again or check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
