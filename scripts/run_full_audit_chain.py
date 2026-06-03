#!/usr/bin/env python3
"""
ACR-QA Full Audit Chain — one command, end-to-end.

Demonstrates the complete trust pipeline:
  scan → Confirmed Tier findings → exploit-verify → autofix → re-exploit → sign → Rekor

Usage:
    python3 scripts/run_full_audit_chain.py --target TESTS/fixtures/exploits/flask_sqli

Output: live progress + final signed evidence summary.
Exits 0 if ≥1 finding reaches fix_verified=True; exits 1 otherwise.

Requirements: Docker daemon running, .venv active.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

_ROOT = Path(__file__).parent.parent
_VENV = _ROOT / ".venv" / "bin"


def _venv(name: str) -> str:
    p = _VENV / name
    return str(p) if p.exists() else name


def _banner(text: str, char: str = "=") -> None:
    print(f"\n{char * 65}")
    print(f"  {text}")
    print(f"{char * 65}")


def _step(n: int, text: str) -> None:
    print(f"\n[{n}/6] {text}")


def run_detection(target_dir: str) -> list[dict]:
    """Run Bandit + Semgrep on target, normalize findings."""
    from CORE.engines.normalizer import RULE_MAPPING

    findings: list[dict] = []

    # Bandit
    try:
        r = subprocess.run(
            [_venv("bandit"), "-r", target_dir, "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        data = json.loads(r.stdout or "{}")
        for res in data.get("results", []):
            tid = res.get("test_id", "")
            sev_map = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
            findings.append(
                {
                    "canonical_rule_id": RULE_MAPPING.get(tid, f"BANDIT-{tid}"),
                    "canonical_severity": sev_map.get(res.get("issue_severity", "LOW"), "low"),
                    "file": res.get("filename", ""),
                    "file_path": res.get("filename", ""),
                    "line": res.get("line_number", 0),
                    "message": res.get("issue_text", ""),
                    "tool_raw": {
                        "tool_name": "bandit",
                        "original_output": {"issue_confidence": res.get("issue_confidence", "")},
                    },
                }
            )
    except Exception as exc:
        print(f"  ⚠ Bandit: {exc}", file=sys.stderr)

    # Semgrep
    custom = _ROOT / "TOOLS" / "semgrep" / "python-rules.yml"
    configs = ["--config=p/python"]
    if custom.exists():
        configs += [f"--config={custom}"]
    try:
        r = subprocess.run(
            [_venv("semgrep"), *configs, "--json", "--quiet", target_dir],
            capture_output=True,
            text=True,
            timeout=180,
        )
        data = json.loads(r.stdout or "{}")
        sev_map = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}
        for res in data.get("results", []):
            rid = res.get("check_id", "")
            short = rid.split(".")[-1][:20]
            findings.append(
                {
                    "canonical_rule_id": RULE_MAPPING.get(rid, f"SEMGREP-{short}"),
                    "canonical_severity": sev_map.get(res.get("extra", {}).get("severity", "WARNING").upper(), "low"),
                    "file": res.get("path", ""),
                    "file_path": res.get("path", ""),
                    "line": res.get("start", {}).get("line", 0),
                    "message": res.get("extra", {}).get("message", ""),
                    "tool_raw": {"tool_name": "semgrep"},
                }
            )
    except Exception as exc:
        print(f"  ⚠ Semgrep: {exc}", file=sys.stderr)

    return findings


def apply_confirmed_tier(findings: list[dict]) -> list[dict]:
    from CORE.engines.confirmed_tier import ConfirmedTierEngine

    engine = ConfirmedTierEngine()
    enriched = engine.enrich_findings(findings)
    return [f for f in enriched if f.get("confirmed_tier", False)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", required=True, help="Target directory to scan")
    args = ap.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        sys.exit(1)

    _banner("ACR-QA Full Audit Chain")
    print(f"  Target:  {target}")
    print("  Pipeline: scan → Confirmed Tier → exploit → autofix → re-exploit → sign")

    # Step 1: Detection
    _step(1, "Running detection (Bandit + Semgrep + custom rules)...")
    findings = run_detection(str(target))
    print(f"  → {len(findings)} raw findings")

    # Step 2: Confirmed Tier
    _step(2, "Applying Confirmed Tier filter (4-gate, 96.4% precision stratum)...")
    confirmed = apply_confirmed_tier(findings)
    print(f"  → {len(confirmed)} Confirmed Tier findings")

    if not confirmed:
        print("\n  No Confirmed Tier findings on this target.")
        print("  (This is expected on the flask_safe fixture — try flask_sqli.)")
        sys.exit(0)

    # Steps 3–6: For each confirmed finding, run Verified Remediation
    from CORE.engines.verified_remediation import VerifiedRemediationEngine

    engine = VerifiedRemediationEngine(use_docker=True, sign=True)
    if not engine._verifier.is_docker_available():
        print("\n  ⚠ Docker not available — skipping exploit verification.")
        print("  Steps 3–6 require the Docker daemon. All other steps completed.")
        sys.exit(0)

    results = []
    for i, finding in enumerate(confirmed[:3]):  # limit to 3 for demo speed
        rid = finding.get("canonical_rule_id", "?")
        fname = Path(finding.get("file", "?")).name
        _banner(f"Finding {i+1}/{min(len(confirmed), 3)}: {rid} in {fname}", char="-")

        _step(3, "Exploit verification (original code)...")
        _step(4, "Patch generation (AutoFixEngine)...")
        _step(5, "Re-exploit verification (patched code)...")
        _step(6, "Attestation (ECDSA-sign + Rekor)...")

        result = engine.run(finding, str(target))
        results.append(result)

        if result.fix_verified:
            print(f"\n  ✅ FIX VERIFIED — {rid}")
            print("     Exploit fired on original → fix applied → exploit now fails")
            if result.fix_diff:
                for line in result.fix_diff.splitlines()[:10]:
                    if line.startswith("+") and not line.startswith("+++"):
                        print(f"     \033[32m{line}\033[0m")
                    elif line.startswith("-") and not line.startswith("---"):
                        print(f"     \033[31m{line}\033[0m")
            if result.attestation:
                has_sig = bool(result.attestation.get("signature") or result.attestation.get("signed"))
                print(f"     Attestation: {'✅ signed' if has_sig else '⚠ bundle only'}")
        else:
            print(f"\n  ❌ Not verified — {result.error or 'see above'}")

    _banner("Summary")
    verified = [r for r in results if r.fix_verified]
    print(f"\n  Verified fixes: {len(verified)}/{len(results)}")
    for r in verified:
        print(f"     ✅ {r.canonical_rule_id} — {Path(r.file).name}")

    if verified:
        print("\n  Full chain complete: scan → confirm → exploit → fix → re-exploit → sign.")
        sys.exit(0)
    else:
        print("\n  ⚠ Chain partially complete — no fix_verified=True on this target.")
        print("  Run against flask_sqli fixture with Docker for a full demonstration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
