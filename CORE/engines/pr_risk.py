"""
ACR-QA PR Risk Score (v5.0.0 Phase A.5 — Review-Bottleneck Solver).

Single 0..100 number per PR. Composes signals we already have so a senior
reviewer can fast-rank 14 open PRs at 7pm without reading each one line by line.

Composition (weights sum = 1.0; runtime-asserted):

    high_count_norm        — number of HIGH findings, capped at HIGH_CAP (10)
    reachability_gate_norm — fraction of HIGH findings whose containing function
                              is reachable from an entry point (per
                              CORE/engines/reachability)
    exploit_verified_norm  — fraction of HIGH findings with exploit_tier =
                              "verified-exploitable" (per exploit_verifier)
    taint_touches_norm     — fraction of HIGH findings with a non-empty
                              taint_path (per taint_analyzer)
    file_risk_avg_norm     — average file-level Heuristic Risk Predictor score
                              for the touched files (0..100 → /100)
    size_penalty_norm      — PR size in changed lines, capped at SIZE_CAP (300)

Weights are deliberately top-heavy on the *current* exploitable signal
(verified-exploitable + reachability) rather than the structural signals.

Honest scope (NOT in v5.0.0 A5):
    - No team-trust delta (Phase B).
    - No cross-PR consolidation (Phase B).
    - No git-blame integration here — the predictor operates on the findings
      list + an optional pr_meta dict from the caller.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

HIGH_CAP: int = 10
SIZE_CAP: int = 300  # PR changed lines; 30 = "ideal", 300 = "definitely too big"

WEIGHTS: dict[str, float] = {
    "high_count": 0.20,
    "reachability_gate": 0.20,
    "exploit_verified": 0.20,
    "taint_touches": 0.10,
    "file_risk_avg": 0.15,
    "size_penalty": 0.15,
}

assert math.isclose(
    sum(WEIGHTS.values()), 1.0, rel_tol=1e-9
), f"PR-risk WEIGHTS must sum to 1.0 (got {sum(WEIGHTS.values())})"


@dataclass
class PRRiskInputs:
    """Single struct the predictor consumes. Caller fills from DB / pipeline."""

    high_count: int = 0
    reachable_high_count: int = 0
    exploit_verified_count: int = 0
    taint_path_count: int = 0
    file_risk_scores: list[int] | None = None  # 0..100 per touched file
    changed_lines: int = 0


@dataclass
class PRRiskResult:
    score: int
    band: str  # "green" 0-30 / "amber" 31-60 / "red" 61-100
    contributions: dict[str, float]
    inputs: dict
    explainer: list[str]  # human-readable reasons, top-down

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "band": self.band,
            "contributions": self.contributions,
            "inputs": self.inputs,
            "explainer": self.explainer,
        }


def _safe_frac(num: int, denom: int) -> float:
    if denom <= 0:
        return 0.0
    return max(0.0, min(1.0, num / denom))


def _band(score: int) -> str:
    if score <= 30:
        return "green"
    if score <= 60:
        return "amber"
    return "red"


def normalize_inputs(inp: PRRiskInputs) -> dict[str, float]:
    high_norm = max(0.0, min(1.0, inp.high_count / HIGH_CAP))
    reach_norm = _safe_frac(inp.reachable_high_count, inp.high_count)
    expl_norm = _safe_frac(inp.exploit_verified_count, inp.high_count)
    taint_norm = _safe_frac(inp.taint_path_count, inp.high_count)
    file_risk_avg = (
        (sum(inp.file_risk_scores) / max(1, len(inp.file_risk_scores))) / 100.0 if inp.file_risk_scores else 0.0
    )
    file_risk_avg = max(0.0, min(1.0, file_risk_avg))
    size_norm = max(0.0, min(1.0, inp.changed_lines / SIZE_CAP))
    return {
        "high_count": high_norm,
        "reachability_gate": reach_norm,
        "exploit_verified": expl_norm,
        "taint_touches": taint_norm,
        "file_risk_avg": file_risk_avg,
        "size_penalty": size_norm,
    }


def _build_explainer(inp: PRRiskInputs, norm: dict[str, float]) -> list[str]:
    """Top-down list of reasons in plain English."""
    out: list[str] = []
    if inp.exploit_verified_count > 0:
        out.append(
            f"{inp.exploit_verified_count} HIGH finding(s) are exploit-verified — " f"do not merge without a fix.",
        )
    if inp.high_count > 0 and inp.reachable_high_count == inp.high_count:
        out.append(f"All {inp.high_count} HIGH findings are in reachable code paths.")
    elif inp.high_count > 0 and inp.reachable_high_count > 0:
        out.append(
            f"{inp.reachable_high_count} of {inp.high_count} HIGH findings are reachable "
            f"from an entry point; others are dead-code.",
        )
    if inp.taint_path_count > 0:
        out.append(f"{inp.taint_path_count} finding(s) have an attacker-controlled taint path.")
    if inp.changed_lines > SIZE_CAP // 2:
        out.append(
            f"PR is large ({inp.changed_lines} lines changed) — consider splitting "
            f"into smaller, reviewable units (target ≤ 30 lines).",
        )
    elif inp.changed_lines > 30:
        out.append(f"PR is {inp.changed_lines} lines; ideal review size is ≤ 30.")
    if inp.file_risk_scores:
        avg = sum(inp.file_risk_scores) / len(inp.file_risk_scores)
        if avg >= 60:
            out.append(f"Touched files have high heuristic risk (avg {int(avg)}/100).")
    return out


def predict_pr_risk(inp: PRRiskInputs) -> PRRiskResult:
    norm = normalize_inputs(inp)
    contributions = {k: round(WEIGHTS[k] * norm[k], 4) for k in WEIGHTS}
    raw = sum(contributions.values())
    score = int(round(max(0.0, min(1.0, raw)) * 100))
    return PRRiskResult(
        score=score,
        band=_band(score),
        contributions=contributions,
        inputs=asdict(inp),
        explainer=_build_explainer(inp, norm),
    )


# ── Convenience: build PRRiskInputs from a findings list + pr_meta ────────────


def inputs_from_findings(
    findings: list[dict],
    file_risk_scores: list[int] | None = None,
    changed_lines: int = 0,
) -> PRRiskInputs:
    """Project a list of CanonicalFinding-shaped dicts into PRRiskInputs."""
    high = 0
    reachable_high = 0
    exploit_verified = 0
    taint = 0
    for f in findings:
        sev = (f.get("canonical_severity") or f.get("severity") or "").lower()
        if sev not in ("high", "critical"):
            continue
        high += 1
        reach = (f.get("reachability_status") or "").lower()
        if reach in ("reachable", "via-config", ""):
            # "" = unknown → treat as reachable per the reachability engine's
            # safe-default policy (don't penalise).
            reachable_high += 1
        exploit = (f.get("exploit_tier") or "").lower()
        if exploit == "verified-exploitable":
            exploit_verified += 1
        if f.get("taint_path"):
            taint += 1
    return PRRiskInputs(
        high_count=high,
        reachable_high_count=reachable_high,
        exploit_verified_count=exploit_verified,
        taint_path_count=taint,
        file_risk_scores=file_risk_scores or [],
        changed_lines=changed_lines,
    )
