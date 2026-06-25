#!/usr/bin/env python3
"""RealVuln miss-report — the rule-discovery engine.

Reads the findings ACR-QA already produced (scan-results/{slug}/{scanner}/results.json),
matches them against ground truth with the SAME logic as run_realvuln_hybrid.py, and tells
you exactly:

  * FN — every real vulnerability you MISSED (file:line, CWE, class, why-it's-a-vuln + snippet)
  * FP — everything you flagged that matched no GT entry (file:line, CWE, source + snippet)

…grouped by repo and aggregated by CWE so the highest-leverage gaps surface first. This
replaces eyeballing all 22 repos to find what to fix next.

It also splits DEV (the 6 repos detectors were built against) vs UNSEEN (held-out proxy),
so you can see whether a gap is a generalization opportunity or just DEV-set tuning.

Usage:
  # Report on every repo that has results + GT
  python scripts/realvuln_miss_report.py --all

  # Only the held-out (UNSEEN) repos — the honest generalization view
  python scripts/realvuln_miss_report.py --unseen

  # Only DEV repos, or specific slugs
  python scripts/realvuln_miss_report.py --dev
  python scripts/realvuln_miss_report.py --repos realvuln-dvpwa realvuln-vampi

  # Machine-readable artifact for run-to-run diffing
  python scripts/realvuln_miss_report.py --all --json reports/miss_report.json

Run a scan first (writes the results.json this reads):
  python scripts/run_realvuln_hybrid.py --all --static-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "TESTS/evaluation/realvuln"
REPOS_DIR = EVAL_DIR / "repos"
RESULTS_DIR = EVAL_DIR / "scan-results"

sys.path.insert(0, str(ROOT / "scripts"))

# Reuse the EXACT matching + GT loading the headline number uses, so the FN/FP shown here
# are precisely the ones counted by run_realvuln_hybrid.score_findings.
from run_realvuln_hybrid import _finding_matches_entry, load_gt  # noqa: E402

DEFAULT_SCANNER = "acr-qa-hybrid-v1"
LINE_TOLERANCE = 10

# The 6 repos detectors were developed against (read line-by-line). Everything else is the
# UNSEEN / held-out proxy. Keep this in sync with the methodology note in realvuln_heldout_result.
DEV_SLUGS = {
    "realvuln-dvpwa",
    "realvuln-djangoat",
    "realvuln-vfapi",
    "realvuln-vulnpy",
    "realvuln-vulnerable-tornado-app",
    "realvuln-pythonssti",
}


def _load_findings(slug: str, scanner: str) -> list[dict]:
    """Read the Semgrep-format results.json ACR-QA wrote back to native findings."""
    rf = RESULTS_DIR / slug / scanner / "results.json"
    if not rf.exists():
        return []
    data = json.loads(rf.read_text())
    findings: list[dict] = []
    for r in data.get("results", []):
        meta = r.get("extra", {}).get("metadata", {})
        cwe_list = meta.get("cwe") or []
        if isinstance(cwe_list, str):
            cwe_list = [cwe_list]
        cwe = cwe_list[0] if cwe_list else ""
        m = re.match(r"(CWE-\d+)", str(cwe))
        cwe = m.group(1) if m else str(cwe)
        findings.append(
            {
                "file": (r.get("path") or "").replace("\\", "/"),
                "cwe": cwe,
                "line": (r.get("start") or {}).get("line") or 0,
                "source": meta.get("source", "?"),
                "confidence": meta.get("confidence", "?"),
            }
        )
    return findings


def _snippet(slug: str, rel_file: str, line: int, ctx: int = 1) -> str:
    """Return the source line (± ctx) for `rel_file`:`line`, or '' if unreadable."""
    if not rel_file or not line:
        return ""
    # GT/finding paths may be repo-relative with or without leading dirs; try a few resolutions.
    candidates = [REPOS_DIR / slug / rel_file]
    for p in candidates:
        if p.exists() and p.is_file():
            try:
                lines = p.read_text(errors="replace").splitlines()
            except OSError:
                return ""
            lo = max(0, line - 1 - ctx)
            hi = min(len(lines), line + ctx)
            out = []
            for i in range(lo, hi):
                marker = "→" if (i + 1) == line else " "
                out.append(f"        {marker}{i + 1:>5}| {lines[i].rstrip()[:120]}")
            return "\n".join(out)
    return ""


def _gt_loc(entry: dict) -> tuple[str, int]:
    f = (entry.get("file") or entry.get("filename") or "").replace("\\", "/")
    line = entry.get("start_line") or (entry.get("location") or {}).get("start_line") or entry.get("line") or 0
    return f, line


def analyse_repo(slug: str, scanner: str) -> dict | None:
    """Classify findings vs GT and return FN/FP detail + counts for one repo."""
    gt_tps, gt_fps = load_gt(slug)
    if not gt_tps:
        return None
    findings = _load_findings(slug, scanner)

    matched_tp_idx: set[int] = set()
    matched_trap_idx: set[int] = set()
    fps: list[dict] = []

    for f in findings:
        f_file, f_cwe, f_line = f["file"], f["cwe"], f["line"] or 0
        matched = False
        for i, tp in enumerate(gt_tps):
            if i in matched_tp_idx:
                continue
            if _finding_matches_entry(f_file, f_cwe, f_line, tp, LINE_TOLERANCE):
                matched_tp_idx.add(i)
                matched = True
                break
        if matched:
            continue
        # didn't claim a real vuln → check trap, but either way it's an FP
        trap_hit = None
        for j, trap in enumerate(gt_fps):
            if j in matched_trap_idx:
                continue
            if _finding_matches_entry(f_file, f_cwe, f_line, trap, LINE_TOLERANCE):
                matched_trap_idx.add(j)
                trap_hit = trap.get("id")
                break
        fps.append({**f, "trap_id": trap_hit})

    # Missed real vulns
    fns: list[dict] = []
    for i, tp in enumerate(gt_tps):
        if i in matched_tp_idx:
            continue
        gf, gl = _gt_loc(tp)
        fns.append(
            {
                "id": tp.get("id"),
                "cwe": tp.get("primary_cwe") or (tp.get("acceptable_cwes") or [""])[0],
                "acceptable_cwes": tp.get("acceptable_cwes") or [],
                "file": gf,
                "line": gl,
                "vuln_class": tp.get("vulnerability_class") or tp.get("expected_category") or "",
                "why": ((tp.get("evidence") or {}).get("description") or "")[:240],
            }
        )

    return {
        "slug": slug,
        "is_dev": slug in DEV_SLUGS,
        "gt_total": len(gt_tps),
        "tp": len(matched_tp_idx),
        "fn": fns,
        "fp": fps,
    }


def _print_repo(rep: dict, scanner: str, show_snippets: bool) -> None:
    tag = "DEV" if rep["is_dev"] else "UNSEEN"
    recall = rep["tp"] / rep["gt_total"] if rep["gt_total"] else 0
    prec_den = rep["tp"] + len(rep["fp"])
    prec = rep["tp"] / prec_den if prec_den else 0
    print(f"\n{'=' * 78}")
    print(
        f"  {rep['slug']}  [{tag}]   recall {recall:.0%} ({rep['tp']}/{rep['gt_total']})"
        f"   precision {prec:.0%}   FN={len(rep['fn'])} FP={len(rep['fp'])}"
    )
    print("=" * 78)

    if rep["fn"]:
        print(f"\n  ── MISSED ({len(rep['fn'])}) — real vulns ACR-QA did not flag ──")
        for fn in sorted(rep["fn"], key=lambda x: x["cwe"]):
            cwes = "/".join(fn["acceptable_cwes"]) or fn["cwe"]
            print(f"\n    ✗ {fn['cwe']:<10} {fn['file']}:{fn['line']}  ({fn['vuln_class']})")
            print(f"      accept: [{cwes}]  id={fn['id']}")
            if fn["why"]:
                print(f"      why: {fn['why']}")
            if show_snippets:
                snip = _snippet(rep["slug"], fn["file"], fn["line"])
                if snip:
                    print(snip)

    if rep["fp"]:
        print(f"\n  ── FALSE POSITIVES ({len(rep['fp'])}) — flagged, no GT match ──")
        by_cwe: dict[str, list[dict]] = defaultdict(list)
        for fp in rep["fp"]:
            by_cwe[fp["cwe"]].append(fp)
        for cwe in sorted(by_cwe, key=lambda c: -len(by_cwe[c])):
            locs = ", ".join(f"{fp['file']}:{fp['line']}" for fp in by_cwe[cwe][:6])
            more = f" (+{len(by_cwe[cwe]) - 6} more)" if len(by_cwe[cwe]) > 6 else ""
            trap = sum(1 for fp in by_cwe[cwe] if fp["trap_id"])
            trap_s = f"  [{trap} hit FP-traps]" if trap else ""
            print(f"    {cwe:<10} ×{len(by_cwe[cwe])}{trap_s}  {locs}{more}")


def _aggregate(reports: list[dict]) -> None:
    """Cross-repo leverage ranking: which CWE classes cost the most recall / precision."""

    def _block(title: str, subset: list[dict]) -> None:
        if not subset:
            return
        fn_by_cwe: dict[str, int] = defaultdict(int)
        fn_repos: dict[str, set] = defaultdict(set)
        fp_by_cwe: dict[str, int] = defaultdict(int)
        tp = sum(r["tp"] for r in subset)
        gt = sum(r["gt_total"] for r in subset)
        fp_total = sum(len(r["fp"]) for r in subset)
        for r in subset:
            for fn in r["fn"]:
                fn_by_cwe[fn["cwe"]] += 1
                fn_repos[fn["cwe"]].add(r["slug"].replace("realvuln-", ""))
            for fp in r["fp"]:
                fp_by_cwe[fp["cwe"]] += 1
        recall = tp / gt if gt else 0
        prec = tp / (tp + fp_total) if (tp + fp_total) else 0
        print(f"\n{'#' * 78}")
        print(
            f"  {title}  —  {len(subset)} repos   recall {recall:.1%} ({tp}/{gt})   "
            f"precision {prec:.1%}   total FN={sum(fn_by_cwe.values())} FP={fp_total}"
        )
        print("#" * 78)
        print("\n  TOP MISSED CWEs (highest recall leverage — fix these first):")
        for cwe in sorted(fn_by_cwe, key=lambda c: -fn_by_cwe[c])[:15]:
            repos = ", ".join(sorted(fn_repos[cwe])[:5])
            print(f"    {cwe:<10} {fn_by_cwe[cwe]:>3} missed   across: {repos}")
        print("\n  NOISIEST CWEs (highest precision leverage — gate these):")
        for cwe in sorted(fp_by_cwe, key=lambda c: -fp_by_cwe[c])[:12]:
            print(f"    {cwe:<10} {fp_by_cwe[cwe]:>3} FPs")

    _block("ALL REPOS", reports)
    _block("DEV SET (in-sample — develop here)", [r for r in reports if r["is_dev"]])
    _block("UNSEEN SET (held-out proxy — prove generalization here)", [r for r in reports if not r["is_dev"]])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="every repo with results + GT")
    ap.add_argument("--dev", action="store_true", help="only DEV repos")
    ap.add_argument("--unseen", action="store_true", help="only UNSEEN (held-out proxy) repos")
    ap.add_argument("--repos", nargs="+", metavar="SLUG", help="specific repo slugs")
    ap.add_argument("--scanner", default=DEFAULT_SCANNER, help=f"scanner slug (default {DEFAULT_SCANNER})")
    ap.add_argument("--no-snippets", action="store_true", help="omit source snippets for FNs")
    ap.add_argument("--summary-only", action="store_true", help="skip per-repo detail, show aggregate only")
    ap.add_argument("--json", metavar="PATH", help="also write a machine-readable artifact")
    args = ap.parse_args()

    all_slugs = sorted(
        d.name
        for d in REPOS_DIR.iterdir()
        if d.is_dir() and (EVAL_DIR / "ground-truth" / d.name / "ground-truth.json").exists()
    )
    if args.repos:
        slugs = args.repos
    elif args.dev:
        slugs = [s for s in all_slugs if s in DEV_SLUGS]
    elif args.unseen:
        slugs = [s for s in all_slugs if s not in DEV_SLUGS]
    elif args.all:
        slugs = all_slugs
    else:
        ap.print_help()
        sys.exit(1)

    reports = []
    for slug in slugs:
        rep = analyse_repo(slug, args.scanner)
        if rep is None:
            print(f"  [{slug}] no GT — skipping")
            continue
        if not (RESULTS_DIR / slug / args.scanner / "results.json").exists():
            print(f"  [{slug}] no results.json for scanner '{args.scanner}' — run the hybrid runner first")
        reports.append(rep)

    if not reports:
        print("No repos analysed. Run: python scripts/run_realvuln_hybrid.py --all --static-only")
        sys.exit(1)

    if not args.summary_only:
        for rep in reports:
            _print_repo(rep, args.scanner, show_snippets=not args.no_snippets)

    _aggregate(reports)

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(reports, indent=2))
        print(f"\n  → wrote {out}")


if __name__ == "__main__":
    main()
