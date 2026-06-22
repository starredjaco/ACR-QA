#!/usr/bin/env python3
"""Consistency analysis: LLM scanner run-to-run recall variance vs ACR-QA's deterministic output.

RealVuln ships 3 runs per LLM agent because LLMs are non-deterministic. This script reports, per
scanner: mean recall, the stable/intersection recall (found in ALL 3 runs), the per-run min/max,
and cost — so the recall *distribution* is visible, not just an average.

IMPORTANT — read before quoting any number: the honest "scan once" recall is a SINGLE run's recall
(see the min/mean/max columns in main()'s output), NOT the 3-run intersection. The intersection is
mechanically <= any single run, so comparing ACR-QA's single deterministic run to an LLM's
intersection unfairly handicaps the LLM. Against each LLM's *worst single run*, ACR-QA wins only
~5/10 — the top tier (GPT-5.5, Opus 4.6/4.8, Kimi) out-recalls it even on their unluckiest run.
ACR-QA's edge is CONSISTENCY (same finding set every run → auditability, scan-diffing, gate
stability) at $0 — NOT a higher bug count. Do not frame the intersection as "reliable recall #1".

ACR-QA's static engine is deterministic: one run == every run.

Usage (from repo root):
  .venv/bin/python scripts/realvuln_reliable_recall.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RV = Path(__file__).resolve().parent.parent / "TESTS/evaluation/realvuln"
sys.path.insert(0, str(RV))

from parsers import get_parser  # noqa: E402
from scorer.matcher import load_ground_truth, match_findings  # noqa: E402

LLMS = [
    "gpt-5.5-agentic-v1",
    "claude-opus-4-8-agentic-v1",
    "claude-opus-4-6-agentic-v1",
    "claude-sonnet-4-6-agentic-v1",
    "gemini-3.1-pro-agentic-v1",
    "deepseek-v4-pro-agentic-v1",
    "kimi-k2.6-agentic-v1",
    "glm-5-agentic-v1",
    "grok-4.20-reasoning-agentic-v1",
    "qwen-3.5-397b-agentic-v1",
]
ACR = "acr-qa-hybrid-v1"


def runs(repo: str, sc: str) -> list[Path]:
    d = RV / "scan-results" / repo / sc
    return sorted(f for f in d.glob("*.json") if not f.name.endswith(".metrics.json")) if d.exists() else []


def gt_load(r: str):
    return load_ground_truth(str(RV / f"ground-truth/{r}/ground-truth.json"))


def cost(sc: str, repos: list[str]) -> float:
    t = 0.0
    for r in repos:
        d = RV / "scan-results" / r / sc
        if d.exists():
            for mf in d.glob("*.metrics.json"):
                try:
                    t += json.loads(mf.read_text()).get("cost_usd", 0) or 0
                except Exception:
                    pass
    return t


def per_run_sets(sc: str, repos: list[str], n: int = 3):
    """Return (tp_sets, fp_sets) per run index across repos."""
    tp_sets = [set() for _ in range(n)]
    fp_sets = [set() for _ in range(n)]
    for repo in repos:
        rf = runs(repo, sc)
        gt = gt_load(repo)
        for ri in range(min(n, len(rf))):
            for r in match_findings(get_parser(sc).parse(str(rf[ri])), gt):
                key = (
                    repo,
                    getattr(r.scanner_finding, "file", ""),
                    getattr(r.scanner_finding, "line", 0),
                    getattr(r.scanner_finding, "cwe", ""),
                )
                if r.classification == "TP":
                    tp_sets[ri].add((repo, r.ground_truth_id))
                elif r.classification == "FP":
                    fp_sets[ri].add(key)
    return tp_sets, fp_sets


def total_gt(repos: list[str]) -> int:
    return sum(sum(1 for e in gt_load(r)["findings"] if e.get("is_vulnerable", True)) for r in repos)


def f2(p: float, r: float) -> float:
    return 5 * p * r / (4 * p + r) if (p + r) else 0.0


def main() -> None:
    allr = [p.name for p in sorted((RV / "ground-truth").iterdir()) if (p / "ground-truth.json").exists()]
    # Common set: ACR-QA + all listed LLMs have >=3 runs (apples-to-apples)
    common = [r for r in allr if runs(r, ACR) and all(len(runs(r, sc)) >= 3 for sc in LLMS)]
    TG = total_gt(common)
    print(f"Reliable-recall leaderboard — {len(common)} repos, {TG} ground-truth TPs (all scanners present)")
    print(f"{'Scanner':<30}{'mean-R':>8}{'RELIABLE-R':>11}{'reliable-F2':>12}{'cost$':>8}")

    rows = []
    # ACR-QA — deterministic: single run is the reliable set
    acr_tp = set()
    acr_fp = 0
    for repo in common:
        for r in match_findings(get_parser(ACR).parse(str(runs(repo, ACR)[0])), gt_load(repo)):
            if r.classification == "TP":
                acr_tp.add((repo, r.ground_truth_id))
            elif r.classification == "FP":
                acr_fp += 1
    acr_r = len(acr_tp) / TG
    acr_p = len(acr_tp) / (len(acr_tp) + acr_fp) if (len(acr_tp) + acr_fp) else 0
    rows.append((ACR + " (STATIC)", acr_r, acr_r, f2(acr_p, acr_r), 0.0))

    for sc in LLMS:
        tps, fps = per_run_sets(sc, common)
        mean_r = sum(len(s) for s in tps) / 3 / TG
        stable_tp = set(tps[0]) & set(tps[1]) & set(tps[2])
        stable_fp = set(fps[0]) & set(fps[1]) & set(fps[2])
        rel_r = len(stable_tp) / TG
        rel_p = len(stable_tp) / (len(stable_tp) + len(stable_fp)) if (len(stable_tp) + len(stable_fp)) else 0
        rows.append((sc, mean_r, rel_r, f2(rel_p, rel_r), cost(sc, common)))

    rows.sort(key=lambda x: -x[2])  # rank by reliable recall
    for sc, mr, rr, rf2, c in rows:
        star = "  <-- ACR-QA" if "acr-qa" in sc else ""
        print(f"{sc:<30}{mr:>7.1%}{rr:>10.1%}{rf2:>11.1%}{c:>8.2f}{star}")

    print()
    print("RELIABLE-R = vulns found in ALL 3 runs (the 3-run intersection — a CONSISTENCY measure,")
    print("  NOT 'scan-once recall': the intersection is <= any single run. See the PAIRWISE min/max")
    print("  block below for the honest single-run distribution.")

    # Robust pairwise: each LLM on its OWN full shared repo set. Show the HONEST single-run
    # distribution (min/mean/max) — the min is the "scan once, unlucky" number that decides it.
    print()
    print("PAIRWISE — ACR-QA recall vs each LLM's SINGLE-RUN recall distribution, on shared repos:")
    print(f"{'LLM':<30}{'repos':>6}{'ACR-QA':>8}{'LLM-min':>8}{'LLM-mean':>9}{'LLM-max':>8}{'beats worst?':>13}")
    beats_worst = 0
    for sc in LLMS:
        repos = [r for r in allr if len(runs(r, sc)) >= 3 and runs(r, ACR)]
        if not repos:
            continue
        tg = total_gt(repos)
        a_tp = set()
        for repo in repos:
            for r in match_findings(get_parser(ACR).parse(str(runs(repo, ACR)[0])), gt_load(repo)):
                if r.classification == "TP":
                    a_tp.add((repo, r.ground_truth_id))
        a_r = len(a_tp) / tg
        tps, _ = per_run_sets(sc, repos)
        run_recalls = [len(s) / tg for s in tps]
        win = a_r > min(run_recalls)
        beats_worst += win
        print(
            f"{sc:<30}{len(repos):>6}{a_r:>7.1%}{min(run_recalls):>8.1%}"
            f"{sum(run_recalls) / 3:>9.1%}{max(run_recalls):>8.1%}{('yes' if win else 'no'):>13}"
        )
    print(
        f"\nACR-QA beats the WORST single run of {beats_worst}/{len(LLMS)} LLMs. "
        "The top tier out-recalls it per scan; ACR-QA's edge is determinism + $0, not bug count."
    )


if __name__ == "__main__":
    main()
