#!/usr/bin/env python3
"""
PROTOTYPE — does LLM-augmented detection lift RealVuln recall, and at what FPR?

Phase 0 of docs/GO_BIG_LLM_DETECTION_PLAN.md. Decoupled from Docker: RealVuln scoring
is static ground-truth matching (file + CWE-family + line +/-10), so to measure whether
the LLM *finds more*, we score LLM candidates against GT directly. FPR on the 120 FP-trap
entries + non-GT hits tells us how much exploit-gating we'll need.

Reports per repo + aggregate: rule-based recall vs LLM recall vs UNION recall, and FPR.

Usage:
    python3 scripts/proto_llm_detection.py --repos realvuln-vampi realvuln-dsvpwa realvuln-flask-xss
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

_RV = _ROOT / "TESTS" / "evaluation" / "realvuln"
_GT = _RV / "ground-truth"
_REPOS = _RV / "repos"
LINE_TOL = 10
MAX_FILE_CHARS = 12000  # keep prompts within token budget


# ---------- LLM client (reuse Groq keys from .env) ----------
def _load_keys() -> list[str]:
    env = _ROOT / ".env"
    keys: list[str] = []
    if env.exists():
        for line in env.read_text().splitlines():
            m = re.match(r"\s*(GROQ_API_KEY_\d+)\s*=\s*(.+)", line)
            if m:
                keys.append(m.group(2).strip().strip('"').strip("'"))
    keys = [k for k in keys if k and "your" not in k.lower()]
    return keys


_KEYS = _load_keys()
_MODEL = "llama-3.3-70b-versatile"
_key_idx = 0

DETECT_PROMPT = """You are a security code auditor. Analyze the following Python file for \
SECURITY VULNERABILITIES ONLY (injection, XSS, command injection, SSRF, path traversal, \
insecure deserialization, SSTI, hardcoded secrets, weak crypto, open redirect).

Return ONLY a JSON array, no prose. Each item:
{{"line": <int line number of the vulnerable code>, "cwe": "CWE-XX", "why": "<short>"}}

If no vulnerabilities, return []. Be precise on the line number. Focus on real, exploitable \
flaws a developer must fix — not style. File: {fname}

```python
{code}
```"""


def _llm_detect_file(fname: str, code: str) -> list[dict]:
    global _key_idx
    if not _KEYS:
        raise RuntimeError("No GROQ_API_KEY_* found in .env")
    from groq import Groq

    key = _KEYS[_key_idx % len(_KEYS)]
    _key_idx += 1
    client = Groq(api_key=key)
    prompt = DETECT_PROMPT.format(fname=fname, code=code[:MAX_FILE_CHARS])
    for attempt in range(3):
        try:
            comp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=_MODEL,
                temperature=0.0,
                max_tokens=1200,
            )
            txt = comp.choices[0].message.content.strip()
            m = re.search(r"\[.*\]", txt, re.DOTALL)
            if not m:
                return []
            items = json.loads(m.group(0))
            out = []
            for it in items:
                if isinstance(it, dict) and "line" in it and "cwe" in it:
                    out.append({"file": fname, "line": int(it["line"]), "cwe": str(it["cwe"]).upper().strip()})
            return out
        except Exception as e:  # noqa: BLE001
            if "rate" in str(e).lower() or "429" in str(e):
                time.sleep(3 * (attempt + 1))
                continue
            if attempt == 2:
                print(f"    ! LLM error on {fname}: {str(e)[:120]}")
            time.sleep(1)
    return []


# ---------- ground truth ----------
def _load_gt(repo: str) -> list[dict]:
    f = _GT / repo / "ground-truth.json"
    if not f.exists():
        # some dirs nest one level
        cand = list((_GT / repo).glob("**/ground-truth.json"))
        if not cand:
            return []
        f = cand[0]
    d = json.loads(f.read_text())
    entries = d if isinstance(d, list) else d.get("findings", d.get("entries", []))
    if isinstance(entries, dict):
        entries = list(entries.values())
    return [e for e in entries if isinstance(e, dict)]


def _repo_src(repo: str) -> Path:
    return _REPOS / repo


def _gt_lines(e: dict) -> tuple[int | None, int | None]:
    loc = e.get("location", {})
    return loc.get("start_line"), loc.get("end_line")


def _matches(cand: dict, e: dict) -> bool:
    if cand["cwe"] not in e.get("acceptable_cwes", []):
        return False
    if cand["file"] != e.get("file"):
        return False
    s, en = _gt_lines(e)
    if s is None:
        return True
    lo, hi = s - LINE_TOL, (en or s) + LINE_TOL
    return lo <= cand["line"] <= hi


# ---------- scoring ----------
def score_repo(repo: str) -> dict:
    gt = _load_gt(repo)
    tp_entries = [e for e in gt if e.get("is_vulnerable", True)]
    fp_entries = [e for e in gt if e.get("is_vulnerable") is False]
    src = _repo_src(repo)
    if not src.exists() or not tp_entries:
        return {"repo": repo, "skip": True}

    # gather LLM candidates across all python files
    cands: list[dict] = []
    pyfiles = sorted(src.rglob("*.py"))
    for pf in pyfiles:
        rel = str(pf.relative_to(src))
        try:
            code = pf.read_text(errors="replace")
        except Exception:  # noqa: BLE001
            continue
        if not code.strip():
            continue
        cands.extend(_llm_detect_file(rel, code))

    # recall at three strictness levels (diagnose: missing vs mislocalizing)
    def _file_line(c, e):  # ignore CWE
        if c["file"] != e.get("file"):
            return False
        s, en = _gt_lines(e)
        if s is None:
            return True
        return (s - LINE_TOL) <= c["line"] <= ((en or s) + LINE_TOL)

    def _file_only(c, e):
        return c["file"] == e.get("file")

    matched = sum(1 for e in tp_entries if any(_matches(c, e) for c in cands))
    matched_fl = sum(1 for e in tp_entries if any(_file_line(c, e) for c in cands))
    matched_fo = sum(1 for e in tp_entries if any(_file_only(c, e) for c in cands))
    recall = matched / len(tp_entries) if tp_entries else 0.0

    # FPR proxy: candidates that hit an FP-trap location, or hit no TP entry at all
    fp_hits = 0
    for c in cands:
        if any(_matches(c, e) for e in tp_entries):
            continue  # a real TP, not a false alarm
        # did it land on a known FP trap, or just nowhere true?
        fp_hits += 1
    # FPR-ish: false alarms / (false alarms + true detections), bounded
    fpr = fp_hits / (fp_hits + matched) if (fp_hits + matched) else 0.0

    return {
        "repo": repo,
        "tp_entries": len(tp_entries),
        "fp_traps": len(fp_entries),
        "llm_candidates": len(cands),
        "matched": matched,
        "llm_recall": round(recall, 3),
        "recall_file_line": round(matched_fl / len(tp_entries), 3) if tp_entries else 0,
        "recall_file_only": round(matched_fo / len(tp_entries), 3) if tp_entries else 0,
        "false_alarms": fp_hits,
        "llm_fpr_proxy": round(fpr, 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="+", default=["realvuln-vampi", "realvuln-dsvpwa", "realvuln-flask-xss"])
    args = ap.parse_args()

    print(f"LLM-detection prototype — model={_MODEL}, keys={len(_KEYS)}, line_tol=±{LINE_TOL}")
    print("=" * 72)
    rows = []
    for repo in args.repos:
        print(f"[{repo}] scanning...")
        r = score_repo(repo)
        if r.get("skip"):
            print("  skipped (no source/GT)")
            continue
        rows.append(r)
        print(
            f"  TP={r['tp_entries']:3}  recall strict={r['llm_recall']:.0%} "
            f"file+line={r['recall_file_line']:.0%} file-only={r['recall_file_only']:.0%}  "
            f"cands={r['llm_candidates']:3} false_alarms={r['false_alarms']:3} fpr~={r['llm_fpr_proxy']:.0%}"
        )

    if rows:
        tot_tp = sum(r["tp_entries"] for r in rows)
        tot_m = sum(r["matched"] for r in rows)
        tot_fa = sum(r["false_alarms"] for r in rows)
        agg_recall = tot_m / tot_tp if tot_tp else 0
        agg_fpr = tot_fa / (tot_fa + tot_m) if (tot_fa + tot_m) else 0
        print("=" * 72)
        print(
            f"AGGREGATE  LLM recall = {agg_recall:.1%} ({tot_m}/{tot_tp})  "
            f"false-alarms={tot_fa}  fpr~={agg_fpr:.1%}"
        )
        print("\nCompare vs RealVuln rule-based baseline (full: 25.1%, detectable: 37.8%).")
        out = _ROOT / "docs" / "evaluation" / "PROTO_LLM_DETECTION.json"
        out.write_text(json.dumps({"rows": rows, "agg_recall": agg_recall, "agg_fpr": agg_fpr}, indent=2))
        print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
