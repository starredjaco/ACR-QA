# ACR-QA vs Semgrep CE — Methodology + Baseline

**Status:** v5.0.0 Phase A.4 (May 19, 2026) — **methodology committed; scan results
populated by operator-run.** This document defines the experiment before the
numbers exist so the comparison can't be tuned after seeing results.

## Why Semgrep CE (and not Snyk / SonarQube)?

| Candidate | Why not in A4 |
|---|---|
| **Snyk** | Requires authenticated cloud + paid plan for SAST on private orgs; per-scan API quotas. Phase B (post-launch). |
| **SonarCloud** | Free tier exists but rate-limits and needs PR-bound projects. Phase B. |
| **Semgrep CE** | 100% local, free, OSS rules. Fair baseline: same machine, same target, same time. |

## Scoring rules (pre-registered)

A finding is a **match** if and only if it satisfies all of:

1. Same `file_path` (workspace-relative).
2. Same line ± 3 (per the existing INTEGRITY.md tolerance for AST-level shifts).
3. Same severity class after mapping (HIGH / MEDIUM / LOW) — Semgrep severities
   map as `ERROR → HIGH`, `WARNING → MEDIUM`, `INFO → LOW`.
4. Both detections are on a **ground-truth-labelled vulnerability** for that repo.
   Findings outside the labelled set count toward the precision denominator but
   **never** toward recall.

Findings flagged by only one tool are tracked as `acr_unique` or
`semgrep_unique` rather than declared "false positive" — neither tool's verdict
is treated as oracle.

## Corpus

Same 13-repo corpus used in `evaluation/EVALUATION.md`:

DVPWA · Pygoat · DSVW · VulPy · Django.nV · django-nv · GoVWA · DVNA · DVWS-node ·
JuiceShop · NodeGoat · vulnerable-flask-app · vulnerable-node-app.

Plus the 10 Tier-4 CVE recall YAMLs added in Phases A.3 + A.4 — but those
contribute to the **CVE recall** table, not the **per-tool precision** table.

## Setup

```bash
# Operator-run (~30 min)
pip install semgrep
for yaml in TESTS/evaluation/ground_truth/*.yml; do
  REPO=$(yq -r .local_path "$yaml")
  if [ ! -d "$REPO" ]; then
    echo "skip $REPO (not cloned)"
    continue
  fi
  semgrep --config p/python --config p/javascript --json -o "/tmp/semgrep-$(basename "$REPO").json" "$REPO"
  acrqa scan --target-dir "$REPO" --json --no-ai > "/tmp/acrqa-$(basename "$REPO").json"
done

# Score (deterministic — committed harness)
python scripts/h2h_score.py --semgrep-dir /tmp --acrqa-dir /tmp --write-md
```

## Planned result tables

These will be filled in by `scripts/h2h_score.py --write-md`. Keeping them as
placeholders so the document layout matches the final shape.

### Overall

| Metric | ACR-QA | Semgrep CE | Δ |
|---|---:|---:|---:|
| Precision (HIGH) | _TBD_ | _TBD_ | _TBD_ |
| Recall (ground-truth findings) | _TBD_ | _TBD_ | _TBD_ |
| F1 | _TBD_ | _TBD_ | _TBD_ |
| Median scan time / repo (s) | _TBD_ | _TBD_ | _TBD_ |
| Unique findings (not in other tool) | _TBD_ | _TBD_ | — |

### Per-repo precision (HIGH only)

| Repo | ACR-QA | Semgrep CE |
|---|---:|---:|
| DVPWA | _TBD_ | _TBD_ |
| Pygoat | _TBD_ | _TBD_ |
| DSVW | _TBD_ | _TBD_ |
| VulPy | _TBD_ | _TBD_ |
| ... | ... | ... |

### Honest expectations (before running)

We expect Semgrep CE to:

- **Win** on raw rule count — its `p/python` registry has hundreds more rules
  than ACR-QA's 139+ Python mappings.
- **Lose** on noise / per-rule cap — Semgrep emits every match; ACR-QA caps to
  5 per rule and dedupes across tools.
- **Tie** on classic-pattern catches like `eval()`, hardcoded passwords, etc.

We expect ACR-QA to:

- **Win** on noise-controlled precision via dedup + per-rule cap.
- **Win** on AI-grounded explanations (Semgrep CE has none).
- **Lose** on cross-language polyglot coverage (Semgrep handles Java/Ruby/etc.).

If post-run numbers contradict any of these we'll keep them and write a
postmortem rather than re-tune the experiment.

## What this comparison does NOT prove

- Semgrep Pro (paid) ships proprietary dataflow + reachability; this baseline
  only uses Semgrep CE OSS rules. The comparison is **fair on inputs, fair on
  cost** but not "ACR-QA beats Semgrep Pro."
- A 13-repo corpus does not generalize to "all Python projects." See
  `EVAL_EXPANSION_PLAN.md` Tier 5 (large frameworks) for Phase B continuation.
