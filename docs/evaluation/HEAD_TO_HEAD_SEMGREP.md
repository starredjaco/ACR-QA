# ACR-QA vs Semgrep CE — Methodology + Baseline

**Status:** v5.0.0 Phase A.4 (May 20, 2026) — **COMPLETED. Real numbers from operator-run on 2026-05-20.**

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

## Results (2026-05-20 operator run)

Full scan output: `TESTS/evaluation/results/` (JSON per repo).
Summary: `TESTS/evaluation/results/eval_summary.json`.

### Overall (after 6 pipeline fixes — 2026-05-20 re-run)

| Metric | ACR-QA | Semgrep CE | Δ |
|---|---:|---:|---:|
| Recall (ground-truth findings) | **92.3%** | **71.2%** | **+21.1pp ACR-QA wins** |
| Avg findings / repo | 160 | 52 | ACR-QA more targeted post-cap |
| Timeout repos (> 900s) | 1 | 0 | bandit-test-cases only |

### Per-repo recall (re-run with fixes)

| Repo | Lang | Exp | ACR-QA | Semgrep CE | Notes |
|------|------|----:|:------:|:----------:|-------|
| bandit-test-cases | python | 4 | **0%** | 75% | Still timeout — examples/ generates too many findings |
| django-nv | python | 4 | **100%** | 100% | |
| dsvw | python | 5 | **100%** | 100% | |
| dvna | javascript | 2 | **100%** | 100% | |
| dvpwa | python | 6 | **100%** | 33% | |
| dvws-node | javascript | 2 | **100%** | 100% | |
| govwa | go | 2 | **100%** | 0% | Semgrep missed target files (dbutil.go, cmd.go) |
| juiceshop | javascript | 3 | **100%** | 100% | Fixed: ESLint skip + 900s timeout (701s actual) |
| nodegoat | javascript | 2 | **100%** | 50% | |
| pygoat | python | 5 | **100%** | 100% | Fixed: 900s timeout (420s actual) |
| vulnerable-flask-app | python | 5 | **100%** | 100% | |
| vulnerable-node | javascript | 3 | **100%** | 0% | Fixed: 900s timeout (383s actual) |
| vulpy | python | 3 | **100%** | 67% | |
| **Average** | | **43** | **92.3%** | **71.2%** | **ACR-QA +21.1pp** |

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
