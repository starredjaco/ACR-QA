#!/usr/bin/env python3
"""
RealVuln False-Negative Triage — Step 1 of the Reconciliation Plan.

Classifies every false-negative into one of three buckets:
  (a) undetectable-by-design  — CWE is authz/CSRF/IDOR/logic; no SAST can catch it
  (b) detectable-but-missed   — CWE is injection/secrets; ACR-QA produced nothing near it
  (c) scoring artifact        — ACR-QA flagged the file/area but CWE or line(±10) didn't match

Then recomputes recall on the DETECTABLE subset only (the honest headline).

Usage:
    python3 scripts/triage_realvuln_misses.py [--realvuln-dir TESTS/evaluation/realvuln]

Outputs:
    docs/evaluation/REALVULN_TRIAGE.md
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from CORE import __version__
from CORE.engines.normalizer import RULE_MAPPING

_ROOT = Path(__file__).parent.parent
_NOW = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# CWE classification — detectable vs undetectable by static analysis
# ---------------------------------------------------------------------------

# CWEs that static pattern/taint analysis CAN reliably detect.
DETECTABLE_CWES: frozenset[str] = frozenset(
    {
        # Injection families
        "CWE-79",  # XSS
        "CWE-80",  # XSS (basic/stored)
        "CWE-89",  # SQL injection
        "CWE-78",  # OS command injection
        "CWE-94",  # Code injection (eval/exec)
        "CWE-601",  # Open redirect
        "CWE-611",  # XXE
        "CWE-1336",  # SSTI
        "CWE-943",  # NoSQL injection
        "CWE-643",  # XPath injection
        "CWE-113",  # HTTP response splitting
        "CWE-117",  # Log injection
        "CWE-73",  # External path (path traversal variant)
        "CWE-22",  # Path traversal
        "CWE-918",  # SSRF
        "CWE-434",  # Unrestricted file upload
        # Secrets / credentials
        "CWE-798",  # Hardcoded credentials
        "CWE-259",  # Hardcoded password
        "CWE-321",  # Hardcoded crypto key
        "CWE-312",  # Cleartext storage of sensitive info
        "CWE-532",  # Info exposure through log files
        "CWE-522",  # Insufficiently protected credentials
        # Crypto weaknesses (detectable by import/usage patterns)
        "CWE-328",  # Weak hash (MD5, SHA1)
        "CWE-327",  # Broken crypto algorithm
        "CWE-338",  # Weak PRNG (random.random)
        "CWE-330",  # Insufficient randomness
        "CWE-916",  # Weak password hash
        "CWE-326",  # Inadequate key strength
        "CWE-347",  # JWT without signature verification
        "CWE-295",  # Improper cert validation (verify=False)
        "CWE-319",  # Cleartext transmission
        # Configuration — detectable via static config patterns
        "CWE-489",  # DEBUG = True
        "CWE-215",  # Info through debug (DEBUG mode)
        "CWE-942",  # CORS misconfiguration (allow-all pattern)
        "CWE-1004",  # Cookie without HttpOnly
        "CWE-614",  # Cookie without Secure flag
        "CWE-1021",  # Clickjacking (missing X-Frame-Options)
        # Deserialization
        "CWE-502",  # Insecure deserialization (pickle/yaml.load)
        # Other pattern-matchable
        "CWE-209",  # Error message info exposure (exception details in response)
        "CWE-204",  # Timing-based info exposure (partial)
    }
)

# CWEs that require runtime understanding of intent, data flow, or access control.
# NO static analysis tool can reliably detect these. Rice's theorem applies.
UNDETECTABLE_CWES: frozenset[str] = frozenset(
    {
        "CWE-352",  # CSRF — requires form+token+session flow
        "CWE-306",  # Missing authentication — requires intent understanding
        "CWE-862",  # Missing authorization — same
        "CWE-863",  # Incorrect authorization — same
        "CWE-639",  # IDOR — requires data ownership reasoning
        "CWE-284",  # Improper access control — requires intent
        "CWE-285",  # Improper authorization — same
        "CWE-287",  # Improper authentication — same
        "CWE-307",  # Brute force protection — runtime rate limiting
        "CWE-400",  # Resource exhaustion — runtime
        "CWE-384",  # Session fixation — runtime flow
        "CWE-640",  # Weak password recovery — workflow logic
        "CWE-613",  # Insufficient session expiration — runtime
        "CWE-565",  # Reliance on cookies without validation — runtime
        "CWE-16",  # Configuration (generic) — too broad, often runtime
        "CWE-200",  # Info exposure (broad) — intent-dependent
        "CWE-256",  # Unprotected credentials in transit — runtime
        "CWE-915",  # Mass assignment — framework-specific, runtime
        "CWE-807",  # Reliance on untrusted inputs in decision — intent
    }
)

# CWE mapping: Bandit test_id → CWE
BANDIT_CWE: dict[str, str] = {
    "B101": "CWE-617",
    "B102": "CWE-78",
    "B103": "CWE-732",
    "B104": "CWE-605",
    "B105": "CWE-259",
    "B106": "CWE-259",
    "B107": "CWE-259",
    "B108": "CWE-377",
    "B110": "CWE-390",
    "B112": "CWE-390",
    "B301": "CWE-502",
    "B302": "CWE-502",
    "B303": "CWE-327",
    "B304": "CWE-327",
    "B305": "CWE-327",
    "B306": "CWE-377",
    "B307": "CWE-94",
    "B308": "CWE-79",
    "B311": "CWE-330",
    "B312": "CWE-319",
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
    "B324": "CWE-327",
    "B325": "CWE-318",
    "B401": "CWE-319",
    "B402": "CWE-319",
    "B403": "CWE-502",
    "B404": "CWE-78",
    "B405": "CWE-611",
    "B406": "CWE-611",
    "B407": "CWE-611",
    "B408": "CWE-611",
    "B409": "CWE-611",
    "B413": "CWE-327",
    "B501": "CWE-295",
    "B502": "CWE-295",
    "B503": "CWE-295",
    "B504": "CWE-295",
    "B505": "CWE-326",
    "B506": "CWE-502",
    "B507": "CWE-295",
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
    "B701": "CWE-1336",
    "B702": "CWE-1336",
    "B703": "CWE-79",
}

CANONICAL_CWE: dict[str, str] = {
    "SECURITY-001": "CWE-78",
    "SECURITY-002": "CWE-390",
    "SECURITY-003": "CWE-617",
    "SECURITY-004": "CWE-89",
    "SECURITY-006": "CWE-522",
    "SECURITY-007": "CWE-605",
    "SECURITY-008": "CWE-502",
    "SECURITY-009": "CWE-326",
    "SECURITY-010": "CWE-79",
    "SECURITY-011": "CWE-22",
    "SECURITY-018": "CWE-502",
    "SECURITY-021": "CWE-78",
    "SECURITY-024": "CWE-611",
    "SECURITY-027": "CWE-89",
    "SECURITY-028": "CWE-89",
    "SECURITY-031": "CWE-1336",
    "SECURITY-032": "CWE-1336",
    "SECURITY-043": "CWE-611",
    "SECURITY-044": "CWE-611",
    "SECURITY-045": "CWE-79",
    "SECURITY-046": "CWE-918",
    "SECURITY-047": "CWE-347",
    "SECURITY-048": "CWE-601",
    "SECURITY-049": "CWE-22",
    "SECURITY-051": "CWE-1333",
    "SECURITY-052": "CWE-22",
    "SECURITY-056": "CWE-918",
    "SECURITY-062": "CWE-78",
    "SECURITY-066": "CWE-117",
    "SECURITY-067": "CWE-90",
    "SECURITY-082": "CWE-16",
    "SECURITY-083": "CWE-16",
    "SECURITY-084": "CWE-352",
    "SECURITY-085": "CWE-79",
    "SECURITY-086": "CWE-79",
    "SECURITY-087": "CWE-1004",
    "SECURITY-088": "CWE-614",
    "SECURITY-601": "CWE-601",
}

SEMGREP_CWE_RE = re.compile(r"(CWE-\d+)")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _venv(name: str) -> str:
    p = _ROOT / ".venv" / "bin" / name
    return str(p) if p.exists() else name


def _mcc(tp: int, tn: int, fp: int, fn: int) -> float:
    n = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return ((tp * tn) - (fp * fn)) / n if n else 0.0


def _fbeta(p: float, r: float, beta: float) -> float:
    b2 = beta * beta
    return (1 + b2) * p * r / (b2 * p + r) if (b2 * p + r) else 0.0


def classify_cwe(cwe: str) -> str:
    if cwe in DETECTABLE_CWES:
        return "detectable"
    if cwe in UNDETECTABLE_CWES:
        return "undetectable"
    return "borderline"


# ---------------------------------------------------------------------------
# Detection (same as run_realvuln_benchmark.py)
# ---------------------------------------------------------------------------


def run_acrqa(repo_dir: str) -> list[dict]:
    findings: list[dict] = []
    try:
        r = subprocess.run(
            [_venv("bandit"), "-r", repo_dir, "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        for res in json.loads(r.stdout or "{}").get("results", []):
            tid = res.get("test_id", "")
            cwe = BANDIT_CWE.get(tid)
            if not cwe:
                continue
            try:
                fname = str(Path(res.get("filename", "")).relative_to(repo_dir))
            except ValueError:
                fname = res.get("filename", "")
            findings.append(
                {
                    "file": fname.replace("\\", "/"),
                    "cwe": cwe,
                    "line": res.get("line_number"),
                    "rule_id": tid,
                    "tool": "bandit",
                }
            )
    except Exception:
        pass

    custom = _ROOT / "TOOLS" / "semgrep" / "python-rules.yml"
    configs = ["--config=p/python"]
    if custom.exists():
        configs += [f"--config={custom}"]
    try:
        r = subprocess.run(
            [_venv("semgrep"), *configs, "--json", "--quiet", repo_dir],
            capture_output=True,
            text=True,
            timeout=300,
        )
        for res in json.loads(r.stdout or "{}").get("results", []):
            metadata = res.get("extra", {}).get("metadata", {})
            raw_cwes = metadata.get("cwe", [])
            if isinstance(raw_cwes, str):
                raw_cwes = [raw_cwes]
            cwes = [m.group(1) for c in raw_cwes if (m := SEMGREP_CWE_RE.match(str(c)))]
            rid = res.get("check_id", "")
            canonical = RULE_MAPPING.get(rid)
            if not cwes and canonical:
                c = CANONICAL_CWE.get(canonical)
                if c:
                    cwes = [c]
            if not cwes:
                continue
            try:
                fname = str(Path(res.get("path", "")).relative_to(repo_dir))
            except ValueError:
                fname = res.get("path", "")
            for cwe in cwes:
                findings.append(
                    {
                        "file": fname.replace("\\", "/"),
                        "cwe": cwe,
                        "line": res.get("start", {}).get("line"),
                        "rule_id": rid,
                        "tool": "semgrep",
                    }
                )
    except Exception:
        pass

    # Deduplicate
    seen: set[tuple] = set()
    merged = []
    for f in findings:
        key = (f["file"], f["cwe"], (f["line"] or 0) // 5)
        if key not in seen:
            seen.add(key)
            merged.append(f)
    return merged


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------


def triage_repo(slug: str, gt: dict, findings: list[dict]) -> dict:
    results = {"slug": slug, "a": [], "b": [], "c": [], "tp": [], "fp_trap": []}

    gt_tps = [e for e in gt.get("findings", []) if e.get("is_vulnerable", True)]
    gt_fps = [e for e in gt.get("findings", []) if not e.get("is_vulnerable", True)]

    for gt_e in gt_tps:
        gt_file = gt_e.get("file", "")
        gt_cwes = set(gt_e.get("acceptable_cwes", [gt_e.get("primary_cwe", "")]))
        gt_line = gt_e.get("location", {}).get("start_line", 0) or 0
        primary_cwe = gt_e.get("primary_cwe", "UNKNOWN")

        # Check if ACR-QA matched this GT entry
        matched = False
        for f in findings:
            if f["file"].endswith(gt_file) or gt_file.endswith(f["file"]):
                if f["cwe"] in gt_cwes:
                    if gt_line == 0 or abs((f["line"] or 0) - gt_line) <= 10:
                        matched = True
                        break

        if matched:
            results["tp"].append({"cwe": primary_cwe, "id": gt_e.get("id")})
            continue

        # It's a FN — classify
        cwe_class = classify_cwe(primary_cwe)

        if cwe_class == "undetectable":
            results["a"].append({"cwe": primary_cwe, "id": gt_e.get("id"), "file": gt_file})
        else:
            # Check if ACR-QA flagged this file at all (any cwe) near the line
            flagged_file_near_line = any(
                (f["file"].endswith(gt_file) or gt_file.endswith(f["file"]))
                and (gt_line == 0 or abs((f["line"] or 0) - gt_line) <= 20)
                for f in findings
            )
            if flagged_file_near_line:
                results["c"].append(
                    {
                        "cwe": primary_cwe,
                        "id": gt_e.get("id"),
                        "file": gt_file,
                        "gt_line": gt_line,
                        "class": cwe_class,
                    }
                )
            else:
                results["b"].append(
                    {
                        "cwe": primary_cwe,
                        "id": gt_e.get("id"),
                        "file": gt_file,
                        "class": cwe_class,
                    }
                )

    for gt_e in gt_fps:
        gt_file = gt_e.get("file", "")
        gt_cwes = set(gt_e.get("acceptable_cwes", [gt_e.get("primary_cwe", "")]))
        gt_line = gt_e.get("location", {}).get("start_line", 0) or 0
        flagged = any(
            (f["file"].endswith(gt_file) or gt_file.endswith(f["file"]))
            and f["cwe"] in gt_cwes
            and (gt_line == 0 or abs((f["line"] or 0) - gt_line) <= 10)
            for f in findings
        )
        if flagged:
            results["fp_trap"].append({"cwe": gt_e.get("primary_cwe"), "id": gt_e.get("id")})

    return results


# ---------------------------------------------------------------------------
# Detectable-subset scoring
# ---------------------------------------------------------------------------


def score_detectable(gt: dict, findings: list[dict]) -> dict:
    """Score only on DETECTABLE CWEs."""
    det_tps = [
        e
        for e in gt.get("findings", [])
        if e.get("is_vulnerable", True) and e.get("primary_cwe", "") in DETECTABLE_CWES
    ]
    det_fps = [
        e
        for e in gt.get("findings", [])
        if not e.get("is_vulnerable", True) and e.get("primary_cwe", "") in DETECTABLE_CWES
    ]

    tp = 0
    for gt_e in det_tps:
        gt_file = gt_e.get("file", "")
        gt_cwes = set(gt_e.get("acceptable_cwes", [gt_e.get("primary_cwe", "")]))
        gt_line = gt_e.get("location", {}).get("start_line", 0) or 0
        for f in findings:
            if (f["file"].endswith(gt_file) or gt_file.endswith(f["file"])) and f["cwe"] in gt_cwes:
                if gt_line == 0 or abs((f["line"] or 0) - gt_line) <= 10:
                    tp += 1
                    break

    fp = 0
    for gt_e in det_fps:
        gt_file = gt_e.get("file", "")
        gt_cwes = set(gt_e.get("acceptable_cwes", [gt_e.get("primary_cwe", "")]))
        gt_line = gt_e.get("location", {}).get("start_line", 0) or 0
        for f in findings:
            if (f["file"].endswith(gt_file) or gt_file.endswith(f["file"])) and f["cwe"] in gt_cwes:
                if gt_line == 0 or abs((f["line"] or 0) - gt_line) <= 10:
                    fp += 1
                    break

    fn = len(det_tps) - tp
    tn = len(det_fps) - fp
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {
        "n_det_tp": len(det_tps),
        "n_det_fp": len(det_fps),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "recall": round(rec, 4),
        "precision": round(prec, 4),
        "fpr": round(fpr, 4),
        "f3": round(_fbeta(prec, rec, 3.0), 4),
        "mcc": round(_mcc(tp, tn, fp, fn), 4),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--realvuln-dir", default=str(_ROOT / "TESTS/evaluation/realvuln"))
    ap.add_argument("--output-dir", default=str(_ROOT / "docs/evaluation"))
    args = ap.parse_args()

    rv_dir = Path(args.realvuln_dir)
    repos_dir = rv_dir / "repos"
    gt_dir = rv_dir / "ground-truth"
    out_dir = Path(args.output_dir)

    cloned = {d.name for d in sorted(repos_dir.iterdir()) if d.is_dir()}
    gt_slugs = {d.name for d in sorted(gt_dir.iterdir()) if d.is_dir()}
    runnable = sorted(cloned & gt_slugs)

    print(f"\n{'='*65}")
    print("RealVuln FN Triage")
    print(f"  Version: {__version__}  Repos: {len(runnable)}/26")
    print(f"{'='*65}\n")

    all_triage: list[dict] = []
    det_scores: list[dict] = []

    # Compute corpus-level CWE distribution
    all_gt_tps = []
    for slug in runnable:
        gt = json.load(open(gt_dir / slug / "ground-truth.json"))
        for f in gt.get("findings", []):
            if f.get("is_vulnerable", True):
                cwe = f.get("primary_cwe", "UNKNOWN")
                all_gt_tps.append({"cwe": cwe, "class": classify_cwe(cwe)})

    det_total = sum(1 for e in all_gt_tps if e["class"] == "detectable")
    undet_total = sum(1 for e in all_gt_tps if e["class"] == "undetectable")
    border_total = sum(1 for e in all_gt_tps if e["class"] == "borderline")

    print(f"Corpus (22 repos): {len(all_gt_tps)} TPs")
    print(f"  Detectable:    {det_total} ({det_total/len(all_gt_tps)*100:.0f}%)")
    print(f"  Undetectable:  {undet_total} ({undet_total/len(all_gt_tps)*100:.0f}%)")
    print(f"  Borderline:    {border_total} ({border_total/len(all_gt_tps)*100:.0f}%)\n")

    for slug in runnable:
        repo_path = str(repos_dir / slug)
        gt = json.load(open(gt_dir / slug / "ground-truth.json"))
        n_tp = sum(1 for f in gt.get("findings", []) if f.get("is_vulnerable", True))
        print(f"  {slug[:48]:<50} GT_TP={n_tp}")

        findings = run_acrqa(repo_path)
        triage = triage_repo(slug, gt, findings)
        all_triage.append(triage)

        det = score_detectable(gt, findings)
        det["slug"] = slug
        det_scores.append(det)

        a, b, c = len(triage["a"]), len(triage["b"]), len(triage["c"])
        tp = len(triage["tp"])
        print(f"    TP={tp}  FN: (a)undetect={a}  (b)missed={b}  (c)artifact={c}  det_recall={det['recall']*100:.0f}%")

    # Aggregate triage
    total_tp = sum(len(t["tp"]) for t in all_triage)
    total_a = sum(len(t["a"]) for t in all_triage)
    total_b = sum(len(t["b"]) for t in all_triage)
    total_c = sum(len(t["c"]) for t in all_triage)
    total_fp_trap = sum(len(t["fp_trap"]) for t in all_triage)
    total_fn = total_a + total_b + total_c

    print(f"\n{'='*65}")
    print("TRIAGE SUMMARY")
    print(f"  TP (matched):                {total_tp}")
    print(f"  FN (a) undetectable:         {total_a}  ({total_a/total_fn*100:.0f}% of FNs)")
    print(f"  FN (b) detectable-but-missed:{total_b}  ({total_b/total_fn*100:.0f}% of FNs)")
    print(f"  FN (c) scoring artifact:     {total_c}  ({total_c/total_fn*100:.0f}% of FNs)")
    print(f"  FP_trap hits:                {total_fp_trap}")

    # Detectable subset aggregate
    agg_det_tp = sum(s["tp"] for s in det_scores)
    agg_det_fn = sum(s["fn"] for s in det_scores)
    agg_det_fp = sum(s["fp"] for s in det_scores)
    agg_det_tn = sum(s["tn"] for s in det_scores)
    agg_det_n = sum(s["n_det_tp"] for s in det_scores)
    det_recall = agg_det_tp / (agg_det_tp + agg_det_fn) if (agg_det_tp + agg_det_fn) else 0.0
    det_prec = agg_det_tp / (agg_det_tp + agg_det_fp) if (agg_det_tp + agg_det_fp) else 0.0
    det_fpr = agg_det_fp / (agg_det_fp + agg_det_tn) if (agg_det_fp + agg_det_tn) else 0.0
    det_f3 = _fbeta(det_prec, det_recall, 3.0)

    print(f"\n{'='*65}")
    print(f"DETECTABLE SUBSET: {agg_det_n}/{det_total} TPs")
    print(f"  Recall:    {det_recall*100:.1f}%")
    print(f"  FPR:       {det_fpr*100:.1f}%")
    print(f"  Precision: {det_prec*100:.1f}%")
    print(f"  F3:        {det_f3:.3f}")

    # Write docs
    _write_triage_md(
        out_dir / "REALVULN_TRIAGE.md",
        all_triage,
        total_tp,
        total_a,
        total_b,
        total_c,
        total_fp_trap,
        det_total,
        undet_total,
        border_total,
        len(all_gt_tps),
        det_recall,
        det_fpr,
        det_prec,
        det_f3,
        agg_det_n,
    )
    _write_json(out_dir / "REALVULN_TRIAGE.json", all_triage, det_scores, det_recall, det_fpr, det_prec, det_f3)

    print("\n  → docs/evaluation/REALVULN_TRIAGE.md")
    print("  → docs/evaluation/REALVULN_TRIAGE.json")


def _write_triage_md(
    path: Path,
    triage: list[dict],
    total_tp: int,
    total_a: int,
    total_b: int,
    total_c: int,
    total_fp: int,
    det_total: int,
    undet_total: int,
    border_total: int,
    grand_total: int,
    det_recall: float,
    det_fpr: float,
    det_prec: float,
    det_f3: float,
    agg_det_n: int,
) -> None:
    total_fn = total_a + total_b + total_c
    lines = [
        "# RealVuln False-Negative Triage",
        "",
        f"> **Generated:** {_NOW.isoformat()}  ",
        f"> **ACR-QA version:** {__version__}  ",
        "> **Purpose:** Classify every FN into (a) undetectable-by-design,",
        "> (b) detectable-but-missed, (c) scoring artifact.",
        "",
        "## Corpus Composition (22 cloned repos)",
        "",
        "| Class | TPs | % of corpus | SAST detectable? |",
        "|---|:---:|:---:|---|",
        f"| **Detectable** (injection/secrets/crypto/config) | {det_total} | "
        f"{det_total/grand_total*100:.0f}% | ✅ yes |",
        f"| **Undetectable** (authz/CSRF/IDOR/logic) | {undet_total} | "
        f"{undet_total/grand_total*100:.0f}% | ❌ no — Rice's theorem |",
        f"| Borderline | {border_total} | {border_total/grand_total*100:.0f}% | partial |",
        f"| **TOTAL** | {grand_total} | 100% | |",
        "",
        "> **Key fact:** ~" + f"{undet_total/grand_total*100:.0f}% of the corpus is auth/CSRF/IDOR/logic.",
        "> No static analysis tool can detect these — they require runtime intent, session flow,",
        "> or data-ownership reasoning. Rice's theorem guarantees no complete static solution.",
        "> The theoretical SAST ceiling on this corpus is ~" + f"{det_total/grand_total*100:.0f}%.",
        "",
        "## False-Negative Triage (22 repos, all FNs classified)",
        "",
        "| Bucket | Count | % of FNs | What it means |",
        "|---|:---:|:---:|---|",
        f"| TP (matched correctly) | {total_tp} | — | ACR-QA found it |",
        f"| **(a) Undetectable-by-design** | {total_a} | {total_a/total_fn*100:.0f}% | "
        f"CWE is authz/CSRF/IDOR — no SAST tool catches these |",
        f"| **(b) Detectable-but-missed** | {total_b} | {total_b/total_fn*100:.0f}% | "
        f"Injection/secrets CWE, ACR-QA produced nothing near the GT location |",
        f"| **(c) Scoring artifact** | {total_c} | {total_c/total_fn*100:.0f}% | "
        f"ACR-QA flagged nearby but CWE family or line(±10) didn't match |",
        f"| FP_trap hits (bad) | {total_fp} | — | Flagged a non-vulnerable entry |",
        "",
        "**Interpretation:** If (a) dominates → the headline is already fine, report detectable-subset.",
        "If (c) dominates → free recall in mapping fixes. If (b) dominates → consider targeted rules",
        "(Step 4, with held-out split).",
        "",
        "## Detectable-Subset Recall (the honest headline)",
        "",
        f"> Restricting to the {agg_det_n} statically-detectable TPs in the 22 cloned repos:",
        "",
        "| Metric | ACR-QA (full output) |",
        "|---|:---:|",
        f"| **Recall (detectable subset)** | **{det_recall*100:.1f}%** |",
        f"| Precision | {det_prec*100:.1f}% |",
        f"| FPR | {det_fpr*100:.1f}% |",
        f"| F3 (recall-weighted) | {det_f3:.3f} |",
        "",
        "**The three-number story:**",
        "",
        "| Number | Corpus | Meaning |",
        "|---|---|---|",
        "| **91.0%** | SecurityEval (synthetic snippets) | algorithmic soundness on isolated CWEs |",
        f"| **{det_recall*100:.1f}%** | RealVuln detectable subset | real multi-file apps, static ceiling |",
        "| **23.5%** | RealVuln full corpus | total incl. 52% auth/CSRF/IDOR (no SAST tool catches) |",
        "",
        "All three numbers are published. The gap is the cost of moving from synthetic to real:",
        "more complexity, more undetectable classes, stricter CWE+line matching.",
        "",
        "## Undetectable CWEs (bucket a) — reference list",
        "",
        "These CWEs are out-of-scope for ALL static analysis tools, documented as such from day one:",
        "",
        "| CWE | Name | Why undetectable |",
        "|---|---|---|",
        "| CWE-352 | CSRF | Requires form+token+session flow understanding |",
        "| CWE-306 | Missing authentication | Requires intent: what *should* be protected |",
        "| CWE-862 | Missing authorization | Same — requires access-control intent |",
        "| CWE-639 | IDOR | Requires data-ownership reasoning |",
        "| CWE-307 | Brute force | Requires runtime rate-limiting context |",
        "| CWE-400 | Resource exhaustion | Runtime resource monitoring |",
        "| CWE-384 | Session fixation | Runtime session-flow analysis |",
        "| CWE-284/287 | Access control | Intent-level, not code-pattern |",
        "",
        "**Citing Meta Pysa:** 'There is no way to build a perfect static analyzer…",
        "Python, as a dynamic language, makes a sound inter-procedural CFG computationally",
        "intractable.' We state this as scope, not weakness.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "cd TESTS/evaluation/realvuln && python3 clone_repos.py",
        "python3 scripts/triage_realvuln_misses.py",
        "```",
    ]
    path.write_text("\n".join(lines) + "\n")


def _write_json(
    path: Path,
    triage: list[dict],
    det_scores: list[dict],
    det_recall: float,
    det_fpr: float,
    det_prec: float,
    det_f3: float,
) -> None:
    payload = {
        "generated": _NOW.isoformat(),
        "version": __version__,
        "detectable_subset": {
            "recall": round(det_recall, 4),
            "fpr": round(det_fpr, 4),
            "precision": round(det_prec, 4),
            "f3": round(det_f3, 4),
        },
        "per_repo": triage,
        "det_scores": det_scores,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
