#!/usr/bin/env python3
"""Hybrid (static + LLM) benchmark runner for RealVuln.

Usage:
  # Test on 3 repos
  python scripts/run_realvuln_hybrid.py --repos dvpwa djangoat vulpy

  # All 22 repos
  python scripts/run_realvuln_hybrid.py --all

  # LLM only (skip static)
  python scripts/run_realvuln_hybrid.py --all --llm-only

  # Static only
  python scripts/run_realvuln_hybrid.py --all --static-only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "TESTS/evaluation/realvuln"
REPOS_DIR = EVAL_DIR / "repos"
GT_DIR = EVAL_DIR / "ground-truth"
RESULTS_DIR = EVAL_DIR / "scan-results"

sys.path.insert(0, str(ROOT / "scripts"))


# ── Ground-truth loader ───────────────────────────────────────────────────────


def load_gt(slug: str) -> tuple[list[dict], list[dict]]:
    gt_file = GT_DIR / slug / "ground-truth.json"
    if not gt_file.exists():
        return [], []
    data = json.loads(gt_file.read_text())
    if isinstance(data, dict):
        entries = data.get("vulnerabilities") or data.get("findings") or []
    else:
        entries = data
    tps = [e for e in entries if e.get("is_vulnerable", True)]
    fps = [e for e in entries if not e.get("is_vulnerable", True)]
    return tps, fps


# ── Static scanner ────────────────────────────────────────────────────────────


def run_static(repo_path: Path, slug: str) -> list[dict]:
    """Run Bandit + Semgrep boost rules; return normalised findings."""
    findings: list[dict] = []

    BANDIT_CWE = {
        "B101": "CWE-703",
        "B102": "CWE-78",
        "B103": "CWE-732",
        "B104": "CWE-605",
        "B105": "CWE-259",
        "B106": "CWE-259",
        "B107": "CWE-259",
        "B108": "CWE-377",
        "B110": "CWE-390",
        "B112": "CWE-390",
        "B201": "CWE-94",
        "B202": "CWE-94",
        "B301": "CWE-502",
        "B302": "CWE-502",
        "B303": "CWE-327",
        "B304": "CWE-327",
        "B305": "CWE-327",
        "B306": "CWE-377",
        "B307": "CWE-78",
        "B311": "CWE-338",
        "B312": "CWE-605",
        "B313": "CWE-611",
        "B314": "CWE-611",
        "B315": "CWE-611",
        "B316": "CWE-611",
        "B317": "CWE-611",
        "B318": "CWE-611",
        "B319": "CWE-611",
        "B320": "CWE-611",
        "B321": "CWE-319",
        "B322": "CWE-78",
        "B323": "CWE-295",
        "B324": "CWE-328",
        "B325": "CWE-338",
        "B401": "CWE-319",
        "B402": "CWE-319",
        "B403": "CWE-502",
        "B404": "CWE-78",
        "B405": "CWE-611",
        "B406": "CWE-611",
        "B407": "CWE-611",
        "B408": "CWE-611",
        "B409": "CWE-611",
        "B410": "CWE-611",
        "B411": "CWE-319",
        "B412": "CWE-78",
        "B413": "CWE-327",
        "B501": "CWE-295",
        "B502": "CWE-326",
        "B503": "CWE-326",
        "B504": "CWE-326",
        "B505": "CWE-326",
        "B506": "CWE-15",
        "B507": "CWE-295",
        "B508": "CWE-319",
        "B509": "CWE-319",
        "B601": "CWE-78",
        "B602": "CWE-78",
        "B603": "CWE-78",
        "B604": "CWE-78",
        "B605": "CWE-78",
        "B606": "CWE-78",
        "B607": "CWE-78",
        "B608": "CWE-89",
        "B609": "CWE-78",
        "B610": "CWE-89",
        "B611": "CWE-89",
        "B612": "CWE-78",
        "B701": "CWE-134",
        "B702": "CWE-79",
        "B703": "CWE-79",
    }

    # Bandit — CURATED high-precision subset only (3rd independent source, feeds the Confirmed tier).
    # Running ALL of Bandit added 330 FPs (22.5% precision); the noisy rules are import/assert/random/
    # try-except. We keep only the syntactically-confident, exploit-relevant rules below. Set
    # ACRQA_RV_BANDIT=full for the whole ruleset (ablation), or =0 to disable.
    _bandit_mode = os.environ.get("ACRQA_RV_BANDIT", "curated")
    if _bandit_mode == "0":
        bandit_cmd = None
    else:
        bandit_cmd = [str(ROOT / ".venv/bin/bandit"), "-r", str(repo_path), "-f", "json", "-q", "--exit-zero"]
    # High-precision rule allowlist (SQLi, shell-injection, deserialization, weak crypto, ssl, jinja).
    _BANDIT_HIGH_PREC = {
        "B608",  # hardcoded SQL → SQLi
        "B602",
        "B604",
        "B605",
        "B606",
        "B609",
        "B611",
        "B610",
        "B612",  # shell / SQL injection
        "B301",
        "B302",
        "B307",  # pickle / marshal / eval deserialization
        "B324",  # weak hash (md5/sha1)
        "B501",
        "B502",
        "B503",
        "B504",  # ssl/tls insecure
        "B201",  # flask debug=True
        "B701",
        "B702",
        "B703",  # jinja2 autoescape / mako / django mark_safe
        "B608",
        "B506",  # SQLi, yaml unsafe load
    }
    try:
        if bandit_cmd is None:
            raise RuntimeError("bandit disabled")
        r = subprocess.run(
            bandit_cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.stdout.strip():
            data = json.loads(r.stdout)
            for issue in data.get("results", []):
                rule = issue.get("test_id", "")
                if _bandit_mode != "full" and rule not in _BANDIT_HIGH_PREC:
                    continue
                cwe = BANDIT_CWE.get(rule)
                if not cwe:
                    continue
                file_abs = issue.get("filename", "")
                try:
                    file_rel = str(Path(file_abs).relative_to(repo_path)).replace("\\", "/")
                except ValueError:
                    file_rel = file_abs.replace("\\", "/")
                findings.append(
                    {
                        "file": file_rel,
                        "cwe": cwe,
                        "line": issue.get("line_number", 0),
                        "source": "bandit",
                    }
                )
    except Exception as e:
        if bandit_cmd is not None:
            print(f"    bandit error: {e}")

    # Semgrep — p/python registry pack + our boost rules. MEASURED (2026-06-23, now that the
    # registry is reachable): adding p/django + p/flask + p/owasp-top-ten was net-NEGATIVE on the
    # 22-repo corpus (precision 47.3%→45.7%, F2 52.3%→52.1%) — p/python + our AST already cover the
    # Python vulns, so the extra packs only add FPs. Same lesson as Bandit-all / generic taint:
    # broad additions hurt, targeted detectors help. Set ACRQA_RV_SEMGREP_PACKS=full for ablation.
    if os.environ.get("ACRQA_RV_SEMGREP_PACKS") == "full":
        semgrep_rules = [
            "p/python",
            "p/django",
            "p/flask",
            "p/owasp-top-ten",
            str(ROOT / "TOOLS/semgrep/realvuln-boost-rules.yml"),
        ]
    else:
        semgrep_rules = ["p/python", str(ROOT / "TOOLS/semgrep/realvuln-boost-rules.yml")]
    for rule in semgrep_rules:
        rule_path = Path(rule)
        if not rule_path.exists() and rule.startswith("/"):
            continue
        try:
            r = subprocess.run(
                ["semgrep", "--config", rule, str(repo_path), "--json", "--quiet", "--no-autofix"],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if r.stdout.strip():
                data = json.loads(r.stdout)
                for item in data.get("results", []):
                    cwe_list = (
                        item.get("extra", {}).get("metadata", {}).get("cwe")
                        or item.get("extra", {}).get("metadata", {}).get("cwe-id")
                        or []
                    )
                    if isinstance(cwe_list, str):
                        cwe_list = [cwe_list]
                    if not cwe_list:
                        continue
                    raw_cwe = cwe_list[0]
                    cwe_match = re.match(r"(CWE-\d+)", str(raw_cwe))
                    if not cwe_match:
                        continue
                    cwe = cwe_match.group(1)
                    file_abs = item.get("path", "")
                    try:
                        file_rel = str(Path(file_abs).relative_to(repo_path)).replace("\\", "/")
                    except ValueError:
                        file_rel = file_abs.replace("\\", "/")
                    findings.append(
                        {
                            "file": file_rel,
                            "cwe": cwe,
                            "line": item.get("start", {}).get("line", 0),
                            "source": "semgrep",
                        }
                    )
        except Exception as e:
            print(f"    semgrep ({rule}) error: {e}")

    # Deduplicate
    seen: set[tuple] = set()
    deduped = []
    for f in findings:
        key = (f["file"], f["cwe"], (f["line"] or 0))
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    return deduped


# ── Confidence tiering (deterministic Confirmed Tier) ──────────────────────────
# FIRM = syntactically clear / taint-gated detectors (high precision by construction).
# TENTATIVE = authorization heuristics (recall-heavy, lower precision — like kolega's auth detectors).
_FIRM_CWES = {
    "CWE-89",
    "CWE-78",
    "CWE-22",
    "CWE-918",
    "CWE-94",
    "CWE-95",
    "CWE-502",
    "CWE-1336",
    "CWE-327",
    "CWE-916",
    "CWE-328",
    "CWE-215",
    "CWE-798",
    "CWE-400",
    "CWE-1333",
    "CWE-16",
    "CWE-532",
    "CWE-338",
    "CWE-330",
    "CWE-259",
    "CWE-256",
    "CWE-287",
    "CWE-522",
    "CWE-284",
    "CWE-601",
    "CWE-643",
    "CWE-295",
    "CWE-614",
    "CWE-1004",
    "CWE-384",
    "CWE-321",
    "CWE-1336",
}
_TENTATIVE_CWES = {"CWE-306", "CWE-862", "CWE-639", "CWE-352", "CWE-307", "CWE-200", "CWE-209", "CWE-204"}


def _confidence_tier(cwe: str, n_sources: int) -> str:
    """Deterministic confidence tier for a finding.
    certain  = corroborated by >=2 independent engines (proven ~79% precision), OR
    firm     = a single syntactically-clear / taint-gated detector,
    tentative= an authorization heuristic (recall-heavy)."""
    if n_sources >= 2:
        return "certain"
    if cwe in _FIRM_CWES:
        return "firm"
    if cwe in _TENTATIVE_CWES:
        return "tentative"
    return "firm"


# ── Scorer ────────────────────────────────────────────────────────────────────


def _entry_locs(entry: dict) -> list[tuple[str, int]]:
    """All candidate (file, line) locations for a GT entry (primary + acceptable_locations)."""
    locs = []
    t_file = (entry.get("file") or entry.get("filename") or "").replace("\\", "/")
    t_line = entry.get("start_line") or (entry.get("location") or {}).get("start_line") or entry.get("line") or 0
    locs.append((t_file, t_line))
    for alt in entry.get("acceptable_locations") or []:
        alt_file = (alt.get("file") or alt.get("filename") or "").replace("\\", "/")
        alt_line = alt.get("start_line") or (alt.get("location") or {}).get("start_line") or alt.get("line") or 0
        if alt_file:
            locs.append((alt_file, alt_line))
    return locs


def _finding_matches_entry(f_file: str, f_cwe: str, f_line: int, entry: dict, tol: int) -> bool:
    t_cwes = entry.get("acceptable_cwes") or [entry.get("primary_cwe") or entry.get("cwe", "")]
    if f_cwe not in t_cwes:
        return False
    for c_file, c_line in _entry_locs(entry):
        if not c_file:
            continue
        if not (f_file.endswith(c_file) or c_file.endswith(f_file)):
            continue
        if abs(f_line - c_line) <= tol:
            return True
    return False


def score_findings(
    findings: list[dict],
    gt_tps: list[dict],
    gt_fps: list[dict],
    line_tolerance: int = 10,
) -> dict:
    """Mirror the official RealVuln matcher: each finding either matches a GT entry
    (TP if is_vulnerable else trap-FP, preferring TP) or matches nothing → FP.
    Each GT entry can be claimed at most once.
    """
    matched_tp_indices: set[int] = set()
    matched_trap_indices: set[int] = set()
    fp_count = 0

    for finding in findings:
        f_file = finding.get("file", "").replace("\\", "/")
        f_cwe_raw = finding.get("cwe", "")
        cwe_m = re.match(r"(CWE-\d+)", f_cwe_raw)
        f_cwe = cwe_m.group(1) if cwe_m else f_cwe_raw
        f_line = finding.get("line") or 0

        # Prefer matching a real TP (so co-located traps don't steal credit)
        matched = False
        for i, tp in enumerate(gt_tps):
            if i in matched_tp_indices:
                continue
            if _finding_matches_entry(f_file, f_cwe, f_line, tp, line_tolerance):
                matched_tp_indices.add(i)
                matched = True
                break
        if matched:
            continue

        # Otherwise see if it hits an FP trap
        for j, trap in enumerate(gt_fps):
            if j in matched_trap_indices:
                continue
            if _finding_matches_entry(f_file, f_cwe, f_line, trap, line_tolerance):
                matched_trap_indices.add(j)
                matched = True
                break

        # No GT match at all → false positive (official semantics)
        if not matched:
            fp_count += 1
        else:
            fp_count += 1  # matched a trap → also a false positive

    tp = len(matched_tp_indices)
    fn = len(gt_tps) - tp
    precision = tp / (tp + fp_count) if (tp + fp_count) > 0 else 0.0
    recall = tp / len(gt_tps) if gt_tps else 0.0
    f2 = (5 * precision * recall) / (4 * precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp_count,
        "fn": fn,
        "total_gt": len(gt_tps),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f2": round(f2, 4),
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def discover_repos() -> list[str]:
    slugs = []
    for d in sorted(REPOS_DIR.iterdir()):
        if d.is_dir() and (GT_DIR / d.name / "ground-truth.json").exists():
            slugs.append(d.name)
    return slugs


def run_repo(slug: str, use_static: bool, use_llm: bool) -> dict:
    repo_path = REPOS_DIR / slug
    gt_tps, gt_fps = load_gt(slug)
    if not gt_tps:
        print(f"  [{slug}] no GT — skipping")
        return {}

    print(f"\n{'='*60}")
    print(f"  {slug}  (GT TPs: {len(gt_tps)}, FP traps: {len(gt_fps)})")
    all_findings: list[dict] = []

    if use_static:
        print("  [static]")
        static_f = run_static(repo_path, slug)
        print(f"    found: {len(static_f)}")
        all_findings.extend(static_f)
        # AST scanner — no API, instant, catches patterns Semgrep misses
        from ast_security_scanner import scan_repo as ast_scan

        ast_f = ast_scan(str(repo_path))
        for f in ast_f:
            f["source"] = "ast"
        print(f"    [ast] found: {len(ast_f)}")
        all_findings.extend(ast_f)

    if use_llm:
        print("  [llm]")
        from llm_security_scanner import scan_repo as llm_scan

        llm_f = llm_scan(str(repo_path), verbose=True)
        for f in llm_f:
            f["source"] = "llm"
        print(f"    found: {len(llm_f)}")
        all_findings.extend(llm_f)

    # Deduplicate across static + LLM, tracking source AGREEMENT per location for confidence tiering.
    from collections import defaultdict

    sources_per_key: dict[tuple, set] = defaultdict(set)
    for f in all_findings:
        key = (f["file"], f["cwe"], (f.get("line") or 0))
        sources_per_key[key].add(f.get("source", "ast"))

    # Corroboration-only sources (e.g. Bandit) UPGRADE confidence when they agree with a primary
    # detector, but a finding flagged ONLY by them is dropped — so they grow the Confirmed tier
    # without polluting recall-mode precision with their standalone false positives.
    # Exact-line dedup (the line//5 bucketing collapsed distinct same-CWE vulns within 5 lines; the
    # official scorer already applies ±10 tolerance, so exact-line is both more accurate and recovers
    # those TPs). A cross-source ±2 merge was tried to claw back near-dup FPs but cost more recall than
    # it saved precision (58.8%→58.4%, held-out −0.5pp), so it was dropped.
    _CORROBORATION_ONLY = {"bandit"}
    seen: set[tuple] = set()
    combined: list[dict] = []
    for f in all_findings:
        key = (f["file"], f["cwe"], (f.get("line") or 0))
        if f.get("source") in _CORROBORATION_ONLY:
            continue
        if sources_per_key[key] <= _CORROBORATION_ONLY:
            continue
        if key not in seen:
            seen.add(key)
            f["confidence"] = _confidence_tier(f["cwe"], len(sources_per_key[key]))
            combined.append(f)

    metrics = score_findings(combined, gt_tps, gt_fps)
    metrics["slug"] = slug
    metrics["findings_count"] = len(combined)
    metrics["static_count"] = len([f for f in combined if f.get("source") != "llm"])
    metrics["llm_count"] = len([f for f in combined if f.get("source") == "llm"])

    # Confidence-tiered metrics: cumulative operating points (kolega's `certain:` done honestly).
    certain = [f for f in combined if f["confidence"] == "certain"]
    certain_firm = [f for f in combined if f["confidence"] in ("certain", "firm")]
    metrics["tier_certain"] = score_findings(certain, gt_tps, gt_fps)
    metrics["tier_certain_firm"] = score_findings(certain_firm, gt_tps, gt_fps)

    print(
        f"  → TP={metrics['tp']}/{metrics['total_gt']} "
        f"recall={metrics['recall']:.1%} precision={metrics['precision']:.1%} "
        f"FP={metrics['fp']}  |  certain P={metrics['tier_certain']['precision']:.0%} "
        f"R={metrics['tier_certain']['recall']:.0%}"
    )

    # Save findings for scorer
    scanner_slug = "acr-qa-hybrid-v1"
    out_dir = RESULTS_DIR / slug / scanner_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    # Convert to Semgrep-compatible format for the existing scorer
    semgrep_results = {"results": []}
    for f in combined:
        semgrep_results["results"].append(
            {
                "check_id": f"acr-qa.{f['cwe'].lower().replace('-', '_')}",
                "path": f["file"],
                "start": {"line": f.get("line") or 0, "col": 1},
                "end": {"line": f.get("line") or 0, "col": 1},
                "extra": {
                    "message": f.get("description", ""),
                    "severity": "ERROR",
                    "metadata": {
                        "cwe": [f["cwe"]],
                        "source": f.get("source", "hybrid"),
                        "confidence": f.get("confidence", "firm"),
                    },
                },
            }
        )
    (out_dir / "results.json").write_text(json.dumps(semgrep_results, indent=2))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos", nargs="+", metavar="SLUG", help="specific repo slugs")
    parser.add_argument("--all", action="store_true", help="run all discovered repos")
    parser.add_argument("--llm-only", action="store_true")
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()

    use_static = not args.llm_only
    use_llm = not args.static_only

    if args.all:
        slugs = discover_repos()
    elif args.repos:
        slugs = args.repos
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Repos: {len(slugs)}  static={use_static}  llm={use_llm}")

    results = []
    for slug in slugs:
        r = run_repo(slug, use_static, use_llm)
        if r:
            results.append(r)

    if not results:
        print("No results.")
        return

    total_tp = sum(r["tp"] for r in results)
    total_gt = sum(r["total_gt"] for r in results)
    total_fp = sum(r["fp"] for r in results)
    recall = total_tp / total_gt if total_gt else 0
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
    f2 = (5 * precision * recall) / (4 * precision + recall) if (precision + recall) > 0 else 0

    print(f"\n{'='*60}")
    print("AGGREGATE RESULTS")
    print(f"  Repos scored:  {len(results)}")
    print(f"  Total GT TPs:  {total_gt}")
    print(f"  Total TP:      {total_tp}")
    print(f"  Total FP:      {total_fp}")
    print(f"  Recall:        {recall:.1%}  ({total_tp}/{total_gt})")
    print(f"  Precision:     {precision:.1%}")
    print(f"  F2:            {f2:.1%}")

    # Confidence-tiered operating points (cumulative) — the deterministic Confirmed Tier.
    print(f"\n  {'Operating point':<22}{'TP':>5}{'FP':>5}{'Recall':>9}{'Prec':>8}{'F2':>7}")
    for label, mkey in [
        ("recall mode (all)", None),
        ("certain+firm", "tier_certain_firm"),
        ("CONFIRMED (certain)", "tier_certain"),
    ]:
        if mkey is None:
            tp, fp = total_tp, total_fp
        else:
            tp = sum(r[mkey]["tp"] for r in results)
            fp = sum(r[mkey]["fp"] for r in results)
        rr = tp / total_gt if total_gt else 0
        pp = tp / (tp + fp) if (tp + fp) else 0
        ff = (5 * pp * rr) / (4 * pp + rr) if (pp + rr) else 0
        print(f"  {label:<22}{tp:>5}{fp:>5}{rr:>8.1%}{pp:>7.1%}{ff:>6.1%}")

    # Per-repo table
    print(f"\n{'Repo':<35} {'GT':>4} {'TP':>4} {'FP':>4} {'Recall':>8} {'Prec':>8}")
    print("-" * 65)
    for r in sorted(results, key=lambda x: -x["recall"]):
        print(
            f"  {r['slug']:<33} {r['total_gt']:>4} {r['tp']:>4} {r['fp']:>4} "
            f"{r['recall']:>7.1%} {r['precision']:>7.1%}"
        )


if __name__ == "__main__":
    main()
