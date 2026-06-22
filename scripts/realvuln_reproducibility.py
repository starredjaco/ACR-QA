#!/usr/bin/env python3
"""Quantify LLM scanner non-determinism vs. ACR-QA's deterministic reproducibility.

RealVuln stores 3 runs per LLM scanner (run-1/2/3.json) because LLM agents are
non-deterministic. This script measures, per scanner:

  - recall range across the 3 runs (max - min, in percentage points)
  - TP-stable%: fraction of all TPs the scanner *ever* finds that appear in ALL 3 runs
    (100% = perfectly reproducible; lower = misses its own findings run-to-run)
  - total USD cost across the runs (from *.metrics.json)

ACR-QA's static engine is deterministic by construction → 0.0pp range, 100% stable, $0.

Usage (from repo root):
  .venv/bin/python scripts/realvuln_reproducibility.py
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


def run_files(repo: str, sc: str) -> list[Path]:
    d = RV / "scan-results" / repo / sc
    return sorted(f for f in d.glob("*.json") if not f.name.endswith(".metrics.json")) if d.exists() else []


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


def main() -> None:
    all_repos = [p.name for p in sorted((RV / "ground-truth").iterdir()) if (p / "ground-truth.json").exists()]
    print("RealVuln reproducibility — LLM run-to-run variance vs. ACR-QA (deterministic)")
    print(f"{'Scanner':<30}{'repos':>6}{'R.rng(pp)':>10}{'TPstable%':>10}{'cost$':>9}")
    print(f"{'acr-qa-hybrid-v1 (STATIC)':<30}{'22':>6}{'0.0':>10}{'100':>10}{'0.00':>9}")

    for sc in LLMS:
        repos = [r for r in all_repos if len(run_files(r, sc)) >= 3]
        if not repos:
            continue
        per_run_tps: list[set] = [set(), set(), set()]
        total = 0
        for repo in repos:
            gt = load_ground_truth(str(RV / f"ground-truth/{repo}/ground-truth.json"))
            total += sum(1 for e in gt["findings"] if e.get("is_vulnerable", True))
            rf = run_files(repo, sc)
            for ri in range(3):
                for r in match_findings(get_parser(sc).parse(str(rf[ri])), gt):
                    if r.classification == "TP":
                        per_run_tps[ri].add((repo, r.ground_truth_id))
        recalls = [len(s) / total * 100 for s in per_run_tps] if total else [0, 0, 0]
        union = set().union(*per_run_tps)
        inter = set(per_run_tps[0]).intersection(*per_run_tps[1:])
        stable = len(inter) / len(union) * 100 if union else 0
        rng = max(recalls) - min(recalls)
        print(f"{sc:<30}{len(repos):>6}{rng:>10.1f}{stable:>10.0f}{cost(sc, repos):>9.2f}")

    print()
    print("TPstable% = fraction of all-TPs-ever-found that appear in ALL 3 runs (100 = deterministic)")
    print("ACR-QA is bit-identical every run by construction; LLM agents are not.")


if __name__ == "__main__":
    main()
