"""
ACR-QA Heuristic Risk Predictor (v5.0.0 Phase A.3).

Per-file risk score (0-100) from six transparent, documented features. This
is NOT machine learning — it is a deterministic weighted linear model with
hand-calibrated weights. The thesis claim is *explainability*, not statistical
accuracy beyond what each feature already implies.

Why no ML?
    - 13-repo corpus is way too small to train anything that generalizes.
    - Reviewers can audit every component of the score (subtract weight × feature).
    - No model drift / no retraining infra / no opaque latent space.

Features (all per-file, normalized to [0, 1] before weighting):
    1. complexity_norm      — cyclomatic complexity (via radon if available, else
                              line count fallback) ÷ COMPLEXITY_CAP (40).
    2. churn_norm           — commits touching the file in the last 90 days
                              ÷ CHURN_CAP (50).
    3. age_norm             — days since first commit ÷ AGE_CAP (365 × 3 = 3 years).
                              Older code is slightly more risky to refactor.
    4. authors_norm         — distinct authors ÷ AUTHORS_CAP (10).
    5. coverage_gap         — 1.0 if no matching test file is found, else 0.0.
                              "Matching" = a file named `test_<basename>.py`,
                              `<basename>_test.py`, or `<basename>.test.{ts,js}`
                              anywhere in the project.
    6. high_density_norm    — current HIGH findings ÷ max(1, LOC / 100). Capped
                              at HIGH_DENSITY_CAP (5 HIGH per 100 LOC) before
                              normalization.

Weights (sum = 1.0):
    0.20 complexity   0.20 churn   0.05 age   0.10 authors
    0.15 coverage gap   0.30 HIGH density

The HIGH-density weight is the heaviest because it is the *current* signal,
not a structural risk proxy. Coverage gap is a strong second because
untested code has the highest engineer-discovery cost.

Determinism:
    Same inputs → same score every time. The engine never calls an LLM.

Performance:
    Score computation per file is O(1). The whole-repo computation cost is
    dominated by per-file complexity analysis (~1-2 ms/file with radon).
"""

from __future__ import annotations

import logging
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Constants (documented + auditable) ────────────────────────────────────────

COMPLEXITY_CAP: int = 40
CHURN_CAP: int = 50
AGE_CAP_DAYS: int = 365 * 3
AUTHORS_CAP: int = 10
HIGH_DENSITY_CAP: float = 5.0  # HIGH findings per 100 LOC

WEIGHTS: dict[str, float] = {
    "complexity": 0.20,
    "churn": 0.20,
    "age": 0.05,
    "authors": 0.10,
    "coverage_gap": 0.15,
    "high_density": 0.30,
}

# Hard invariant — if any future contributor edits WEIGHTS, this must still hold.
assert math.isclose(
    sum(WEIGHTS.values()), 1.0, rel_tol=1e-9
), f"Risk-predictor WEIGHTS must sum to 1.0 (got {sum(WEIGHTS.values())})"


@dataclass
class RiskFeatures:
    file_path: str
    complexity: float = 0.0
    churn_90d: int = 0
    age_days: int = 0
    author_count: int = 0
    test_coverage_gap: int = 0  # 1 = no test file found, 0 = test file present
    high_finding_count: int = 0
    loc: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RiskScore:
    file_path: str
    score: int  # 0..100
    features: dict
    contributions: dict  # weight × normalized — auditable breakdown

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "score": self.score,
            "features": self.features,
            "contributions": self.contributions,
        }


# ── Normalization ─────────────────────────────────────────────────────────────


def _norm(x: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return max(0.0, min(1.0, float(x) / cap))


def normalize_features(f: RiskFeatures) -> dict[str, float]:
    """Return each feature in [0, 1]."""
    high_per_100loc = (f.high_finding_count / max(1, f.loc)) * 100.0
    return {
        "complexity": _norm(f.complexity, COMPLEXITY_CAP),
        "churn": _norm(f.churn_90d, CHURN_CAP),
        "age": _norm(f.age_days, AGE_CAP_DAYS),
        "authors": _norm(f.author_count, AUTHORS_CAP),
        "coverage_gap": 1.0 if f.test_coverage_gap else 0.0,
        "high_density": _norm(high_per_100loc, HIGH_DENSITY_CAP),
    }


# ── Score computation ────────────────────────────────────────────────────────


def predict_score(features: RiskFeatures) -> RiskScore:
    """Compute the 0..100 risk score for a single file from explicit features."""
    norm = normalize_features(features)
    contributions = {k: round(WEIGHTS[k] * norm[k], 4) for k in WEIGHTS}
    raw = sum(contributions.values())
    score = int(round(max(0.0, min(1.0, raw)) * 100))
    return RiskScore(
        file_path=features.file_path,
        score=score,
        features=features.to_dict(),
        contributions=contributions,
    )


# ── Feature extraction helpers ────────────────────────────────────────────────


def _count_loc(path: Path) -> int:
    try:
        return sum(1 for _ in path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return 0


def _complexity_for_file(path: Path) -> float:
    """Sum of cyclomatic complexity across functions in *path*.

    Uses radon when the file is Python; falls back to LOC/20 as a coarse
    proxy for other languages (so a 200-line JS file scores ~10).
    """
    if path.suffix != ".py":
        return _count_loc(path) / 20.0
    try:
        from radon.complexity import cc_visit

        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            results = cc_visit(source)
        except Exception:
            return _count_loc(path) / 20.0
        return float(sum(r.complexity for r in results))
    except Exception:
        return _count_loc(path) / 20.0


def _git_churn_authors_age(repo_dir: Path, rel_path: str) -> tuple[int, int, int]:
    """Return (churn_90d, author_count, age_days) for a tracked file.

    Returns (0, 0, 0) if the file is untracked / git command fails.
    """
    try:
        # Churn — commits in last 90 days
        churn_out = subprocess.run(
            ["git", "-C", str(repo_dir), "log", "--since=90.days", "--oneline", "--", rel_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        churn = len([ln for ln in churn_out.stdout.splitlines() if ln.strip()]) if churn_out.returncode == 0 else 0

        # Authors — distinct over whole history (bounded by --max-count for safety)
        authors_out = subprocess.run(
            ["git", "-C", str(repo_dir), "log", "--max-count=500", "--format=%an", "--", rel_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        authors = (
            len({ln.strip() for ln in authors_out.stdout.splitlines() if ln.strip()})
            if authors_out.returncode == 0
            else 0
        )

        # Age — days since first commit touching this file
        first_out = subprocess.run(
            ["git", "-C", str(repo_dir), "log", "--reverse", "--format=%ct", "--max-count=1", "--", rel_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if first_out.returncode == 0 and first_out.stdout.strip():
            import time as _t

            first_ts = int(first_out.stdout.strip().splitlines()[0])
            age_days = max(0, (int(_t.time()) - first_ts) // 86400)
        else:
            age_days = 0

        return churn, authors, age_days
    except (OSError, subprocess.SubprocessError, ValueError):
        return 0, 0, 0


def _has_test_file(repo_dir: Path, source_path: Path) -> bool:
    """Heuristic: does *source_path* have a matching test file anywhere in the repo?"""
    stem = source_path.stem
    if source_path.suffix == ".py":
        candidates = {f"test_{stem}.py", f"{stem}_test.py"}
    elif source_path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
        candidates = {
            f"{stem}.test{source_path.suffix}",
            f"{stem}.spec{source_path.suffix}",
        }
    else:
        return True  # unknown language → assume covered; don't penalise
    for cand in candidates:
        if next(repo_dir.rglob(cand), None) is not None:
            return True
    return False


# ── High-level scorer over a run ──────────────────────────────────────────────


def score_files(
    repo_dir: str | Path,
    findings: list[dict],
    paths: list[str] | None = None,
) -> list[RiskScore]:
    """Compute a RiskScore for every distinct file_path in *findings* (or *paths*).

    `findings` is a list of CanonicalFinding-shaped dicts (must include
    `file_path` and `canonical_severity`). HIGH findings are counted toward the
    `high_finding_count` feature.

    `paths` lets the caller score a fixed file list independent of findings.
    """
    repo = Path(repo_dir).resolve()
    by_file: dict[str, dict] = {}
    if paths:
        for p in paths:
            by_file.setdefault(p, {"high": 0})
    for f in findings:
        fp = f.get("file_path") or ""
        if not fp:
            continue
        entry = by_file.setdefault(fp, {"high": 0})
        sev = (f.get("canonical_severity") or f.get("severity") or "").lower()
        if sev in ("high", "critical"):
            entry["high"] += 1

    out: list[RiskScore] = []
    for fp, agg in by_file.items():
        src = (repo / fp) if not Path(fp).is_absolute() else Path(fp)
        loc = _count_loc(src) if src.is_file() else 0
        complexity = _complexity_for_file(src) if src.is_file() else 0.0
        churn, authors, age = _git_churn_authors_age(repo, fp)
        has_test = _has_test_file(repo, src) if src.is_file() else True
        features = RiskFeatures(
            file_path=fp,
            complexity=complexity,
            churn_90d=churn,
            age_days=age,
            author_count=authors,
            test_coverage_gap=0 if has_test else 1,
            high_finding_count=int(agg.get("high", 0)),
            loc=loc,
        )
        out.append(predict_score(features))
    out.sort(key=lambda s: (-s.score, s.file_path))
    return out


# ── Convenience for the API endpoint ──────────────────────────────────────────


def risk_map_payload(scores: list[RiskScore]) -> dict:
    """Wrap a list of RiskScore into the JSON shape returned by the endpoint."""
    return {
        "weights": WEIGHTS,
        "caps": {
            "complexity": COMPLEXITY_CAP,
            "churn": CHURN_CAP,
            "age_days": AGE_CAP_DAYS,
            "authors": AUTHORS_CAP,
            "high_density_per_100loc": HIGH_DENSITY_CAP,
        },
        "files": [s.to_dict() for s in scores],
        "total_files": len(scores),
    }
