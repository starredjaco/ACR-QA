#!/usr/bin/env python3
"""
Seed the dashboard with a REAL Go scan so the demo can show all three language
adapters (Python · JavaScript · Go), not just Python/JS.

Why this exists separately from seed_demo_scan.py
-------------------------------------------------
The Go adapter (gosec + staticcheck + semgrep) is fully functional, but the Go code
path in CORE/main.py is CLI-only — it writes findings to a file and does NOT persist
to the database, so a Go scan never reaches the dashboard. Rather than modify the
Python/JS pipeline (risk), this script reuses the GoAdapter and the public Database
API (create_analysis_run / insert_finding / complete_analysis_run / attest) to land a
genuine Go run in the dashboard. Touches no existing pipeline code.

gosec is snap-confined and cannot read /tmp, so the sample is copied into $HOME first.

Usage:  .venv/bin/python3 scripts/seed_go_demo.py [--repo-name go-vuln-demo]
Requires: gosec + staticcheck on ~/.local/gopath/bin (the GoAdapter's expected path).
"""

from __future__ import annotations

import argparse
import dataclasses
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
SAMPLE = PROJECT_ROOT / "TESTS" / "samples" / "go-vuln-demo"
# gosec (snap) can't read /tmp, and Go tooling skips dot-dirs — stage in a plain $HOME dir
WORKDIR = Path.home() / "acrqa-go-demo"


def _to_dict(f) -> dict:
    return dataclasses.asdict(f) if hasattr(f, "__dataclass_fields__") else dict(vars(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-name", default="go-vuln-demo")
    args = ap.parse_args()

    from CORE.adapters.go_adapter import GoAdapter
    from DATABASE.database import Database

    # stage the sample inside $HOME (snap-gosec can't read /tmp)
    if WORKDIR.exists():
        shutil.rmtree(WORKDIR)
    shutil.copytree(SAMPLE, WORKDIR)
    print(f"staged sample → {WORKDIR}")

    adapter = GoAdapter(target_dir=str(WORKDIR))
    avail = adapter.check_tools_available()
    print(f"tools: gosec={avail['gosec']} staticcheck={avail['staticcheck']} semgrep={avail['semgrep']}")
    if not avail["gosec"]:
        print("✗ gosec not found at ~/.local/gopath/bin/gosec — symlink it first.")
        return 1

    results = adapter.run_tools()
    for err in results.get("errors", []):
        print(f"  ⚠ {err}")
    findings_obj = adapter.get_all_findings(results)
    findings = [_to_dict(f) for f in findings_obj]
    print(f"Go adapter produced {len(findings)} findings")
    if not findings:
        print("✗ no findings — nothing to seed.")
        return 1

    db = Database()
    if not db.available():
        print("✗ database unavailable — is Postgres up?")
        return 1

    # reset any prior run of this repo so the seed is idempotent
    try:
        db.execute("DELETE FROM analysis_runs WHERE repo_name = %s", (args.repo_name,))
    except Exception as exc:  # noqa: BLE001
        print(f"  (reset skipped: {exc})")

    run_id = db.create_analysis_run(repo_name=args.repo_name, pr_number=None)
    high = med = low = 0
    for f in findings:
        sev = (f.get("severity") or "low").lower()
        f.setdefault("canonical_rule_id", f.get("rule_id", "GO-UNKNOWN"))
        f.setdefault("category", "security")
        db.insert_finding(run_id, f)
        high += sev == "high"
        med += sev == "medium"
        low += sev not in ("high", "medium")
    db.complete_analysis_run(run_id, len(findings))

    # sign it, like every other run
    try:
        from CORE.engines.attestation import AttestationEngine

        AttestationEngine().attest_scan(
            run_id,
            {
                "repo_name": args.repo_name,
                "total_findings": len(findings),
                "high_count": high,
                "medium_count": med,
                "low_count": low,
                "reachability_enabled": False,
                "verified_exploitable": 0,
                "suppressed_by_embedding": 0,
            },
            db,
        )
        print("  ✓ attestation signed")
    except Exception as exc:  # noqa: BLE001
        print(f"  attestation skipped: {exc}")

    print(
        f"✓ Seeded Go run #{run_id} — {args.repo_name}: {len(findings)} findings "
        f"({high} high · {med} medium · {low} low). Open it in the dashboard."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
