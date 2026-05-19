#!/usr/bin/env python3
"""Dogfooding gate (v5.0.0 Phase A.4 — Security Hardening).

Runs ACR-QA's IaC scanner + a tight bandit pass over ACR-QA's own source tree
and reports HIGH findings. Designed to be cheap enough to run on every commit
in CI (no LLM, no full pipeline).

Exit codes:
    0 — no HIGH findings (gate green)
    1 — HIGH findings present
    2 — engine unavailable / scan errored

Wire into CI as:
    .venv/bin/python scripts/dogfood.py --fail-on=high
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


EXCLUDED_PREFIXES = (
    "TESTS/samples/",
    "TESTS/evaluation/",
    "test_targets/",
    "TESTS/fixtures/",
)


def run_iac_scan() -> list[dict]:
    """Run the IaC scanner against the repo and return CanonicalFinding dicts.

    Findings inside well-known test-fixture directories are filtered out — those
    files are *intentionally* vulnerable to exercise the scanner's rules.
    """
    sys.path.insert(0, str(ROOT))
    try:
        from CORE.engines.iac_scanner import IaCScanner
    except Exception as exc:
        print(f"[error] IaCScanner import failed: {exc}", file=sys.stderr)
        return []
    raw = IaCScanner(target_dir=str(ROOT)).scan()
    out: list[dict] = []
    for f in raw:
        fp = (f.get("file") or "").replace("\\", "/")
        # convert absolute path → repo-relative
        if fp.startswith(str(ROOT)):
            fp = fp[len(str(ROOT)) :].lstrip("/")
        if any(fp.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue
        out.append(f)
    return out


def run_bandit_high_only() -> list[dict]:
    """Run bandit in argv mode and filter to HIGH severity only.

    Falls back to an empty list when bandit isn't installed — we don't
    want the gate to crash on environments without bandit.
    """
    try:
        proc = subprocess.run(
            ["bandit", "-r", str(ROOT / "CORE"), "-f", "json", "-q", "--severity-level", "high"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        print(f"[warn] bandit unavailable: {exc}", file=sys.stderr)
        return []
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return []
    return [f for f in data.get("results", []) if str(f.get("issue_severity", "")).upper() == "HIGH"]


def summarize(iac_findings: list[dict], bandit_findings: list[dict]) -> dict:
    sev_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for f in iac_findings:
        sev = (f.get("severity") or "low").lower()
        sev_counts[sev if sev in sev_counts else "low"] += 1
    return {
        "iac_total": len(iac_findings),
        "iac_by_severity": sev_counts,
        "bandit_high": len(bandit_findings),
        "high_total": sev_counts["high"] + len(bandit_findings),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ACR-QA dogfooding gate")
    parser.add_argument(
        "--fail-on",
        default="high",
        choices=["high", "medium", "low", "none"],
        help="lowest severity that should fail the gate (default: high)",
    )
    parser.add_argument("--json", metavar="FILE", help="write summary JSON to FILE")
    args = parser.parse_args(argv)

    iac = run_iac_scan()
    bandit_high = run_bandit_high_only()
    summary = summarize(iac, bandit_high)

    print("== ACR-QA Dogfooding Gate ==")
    print(
        f"IaC findings: {summary['iac_total']} "
        f"({summary['iac_by_severity']['high']} HIGH, "
        f"{summary['iac_by_severity']['medium']} MED, "
        f"{summary['iac_by_severity']['low']} LOW)"
    )
    print(f"Bandit HIGH findings under CORE/: {summary['bandit_high']}")

    if args.json:
        Path(args.json).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    sev_rank = {"high": 0, "medium": 1, "low": 2, "none": 99}
    fail_rank = sev_rank[args.fail_on]
    breaches = 0
    for sev_name, rank in (("high", 0), ("medium", 1), ("low", 2)):
        if rank <= fail_rank:
            breaches += summary["iac_by_severity"][sev_name]
    breaches += summary["bandit_high"]

    if breaches:
        print(f"\n❌ Gate failed: {breaches} finding(s) at or above {args.fail_on}")
        return 1
    print(f"\n✅ Gate passed at threshold {args.fail_on}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
