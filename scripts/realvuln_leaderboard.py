#!/usr/bin/env python3
"""RealVuln head-to-head leaderboard — score every scanner on the same corpus.

The benchmark ships each scanner's raw findings under
`TESTS/evaluation/realvuln/scan-results/{repo}/{scanner}/results.json`. This tool scores all of them
against ground truth with the SAME matcher the headline number uses (file + CWE + ±10 line) and ranks
them by F2, so ACR-QA's competitive position is reproducible from one command:

    python scripts/realvuln_leaderboard.py                 # deterministic tools + us
    python scripts/realvuln_leaderboard.py --all           # include every scanner dir found

Notes
-----
* A missing results.json for a repo counts as "found nothing there" (0 TP / 0 FP), matching how the
  official corpus scores partial coverage.
* Some LLM-agent result files use a non-Semgrep schema this loader can't parse; they show up with 0
  findings and are flagged `[unparsed]` rather than silently ranked — their real scores live in the
  benchmark's own tooling. The deterministic tools (semgrep/snyk/sonarqube/kolega) parse cleanly and
  are the apples-to-apples peers for a pure-static scanner.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "TESTS/evaluation/realvuln"
SR = EVAL / "scan-results"
GT = EVAL / "ground-truth"
sys.path.insert(0, str(ROOT / "scripts"))

from run_realvuln_hybrid import _finding_matches_entry, load_gt  # noqa: E402

# Repos added only as fresh held-out validation — excluded from the head-to-head so every tool is
# scored on the same shared corpus (competitors have no results for these).
HELD_OUT = {"realvuln-pygoat", "realvuln-owasp-web-playground"}
DETERMINISTIC = {"acr-qa-hybrid-v1", "kolega-enterprise-v1", "kolega-v0.0.1", "semgrep", "snyk", "sonarqube"}
US = "acr-qa-hybrid-v1"


def _load(slug: str, scanner: str) -> list[dict] | None:
    f = SR / slug / scanner / "results.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    out = []
    for r in data.get("results", []) if isinstance(data, dict) else []:
        meta = (r.get("extra", {}) or {}).get("metadata", {}) or {}
        cwe = meta.get("cwe") or meta.get("cwe-id") or r.get("check_id", "")
        if isinstance(cwe, list):
            cwe = cwe[0] if cwe else ""
        m = re.match(r"(CWE-\d+)", str(cwe))
        out.append(
            {
                "file": (r.get("path") or "").replace("\\", "/"),
                "cwe": m.group(1) if m else str(cwe),
                "line": (r.get("start") or {}).get("line") or 0,
            }
        )
    return out


def _score(scanner: str, slugs: list[str]) -> dict:
    tp = fp = gt = 0
    parsed = raw = 0
    for slug in slugs:
        gt_tps, _ = load_gt(slug)
        gt += len(gt_tps)
        findings = _load(slug, scanner)
        if findings is None:
            continue  # no results for this repo → everything here is a miss
        raw += len(findings)
        claimed: set[int] = set()
        for f in findings:
            hit = False
            for i, t in enumerate(gt_tps):
                if i in claimed:
                    continue
                if _finding_matches_entry(f["file"], f["cwe"], f["line"] or 0, t, 10):
                    claimed.add(i)
                    hit = True
                    break
            if not hit:
                fp += 1
        tp += len(claimed)
        parsed += 1
    recall = tp / gt if gt else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    f2 = (5 * prec * recall) / (4 * prec + recall) if (prec + recall) else 0.0
    return {
        "scanner": scanner,
        "recall": recall,
        "prec": prec,
        "f2": f2,
        "tp": tp,
        "fp": fp,
        "raw": raw,
        "repos": parsed,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="include every scanner dir (default: deterministic + us)")
    args = ap.parse_args()

    slugs = sorted(
        d.name
        for d in SR.iterdir()
        if d.is_dir() and (GT / d.name / "ground-truth.json").exists() and d.name not in HELD_OUT
    )
    scanners = sorted({p.name for slug in slugs for p in (SR / slug).iterdir() if p.is_dir()})
    if not args.all:
        scanners = [s for s in scanners if s in DETERMINISTIC]

    rows = sorted((_score(s, slugs) for s in scanners), key=lambda r: -r["f2"])
    print(f"RealVuln leaderboard — {len(slugs)} repos, official matcher (file + CWE + ±10 line)\n")
    print(f"{'scanner':<32}{'recall':>8}{'prec':>8}{'F2':>7}{'TP':>6}{'FP':>7}{'repos':>7}")
    print("-" * 76)
    for r in rows:
        tag = "  <== ACR-QA" if r["scanner"] == US else ("  [unparsed]" if r["raw"] == 0 and r["repos"] else "")
        print(
            f"{r['scanner']:<32}{r['recall']:>7.1%}{r['prec']:>8.1%}{r['f2']:>7.3f}"
            f"{r['tp']:>6}{r['fp']:>7}{r['repos']:>7}{tag}"
        )


if __name__ == "__main__":
    main()
