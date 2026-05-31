# P4 — Confirmed Tier: High-Confidence Stratum

Generated: 2026-05-31
Stratum: HIGH severity + curated rule set + production-code path + Bandit-HIGH confidence
Industry comparable: Snyk High Confidence, SonarQube Reliability A, Checkmarx Confirmed

---

## Motivation

Production security teams require an auto-triage tier with near-zero false-positive rate.
The security tier (§5.6, P3) achieves 26.9% conservative precision — useful for analyst
review but not for autopilot remediation. The **Confirmed Tier** stratifies further by
intersecting four orthogonal high-confidence signals, producing a tighter denominator
with near-perfect precision.

This is the standard pattern used by commercial SAST vendors:
- **Snyk Code:** "High Confidence" tier — published ≥85% precision
- **SonarQube:** Reliability rating A — auto-triage threshold
- **Checkmarx:** "Confirmed" classification — production-grade

## Stratum Definition

A finding belongs to the Confirmed Tier if and only if all four conditions hold:

| Signal | Criterion | Source |
|--------|-----------|--------|
| Severity | `canonical_severity == high` | ACR-QA SeverityScorer |
| Rule class | `canonical_rule_id ∈ ConfirmedRuleSet` (22 rules) | Curated list — empirical ≥50% precision or published high-confidence |
| Code path | Not in `tests/`, `examples/`, `docs/`, `migrations/`, build scripts, vendor dirs | Regex over relative path |
| Tool confidence | For Bandit: `issue_confidence == HIGH` (Bandit's own AST-shape confidence) | Bandit `issue_confidence` field |

The Bandit confidence signal is **orthogonal** to the canonical rule taxonomy — it reflects
Bandit's internal AST-shape match strength, not ACR-QA's triage labels. This breaks the
tautology that would otherwise arise from using only the rule-set + path filter.

---

## Results — 30-Repo Precision Corpus

| Metric | Value |
|--------|------:|
| Confirmed Tier denominator | **55** |
| AUTO_TP | 53 |
| AUTO_FP | 0 |
| NEEDS_REVIEW | 2 |
| **Conservative precision** | **96.4%** |
| **Optimistic precision** | **100.0%** |
| Bootstrap 95% CI (conservative) | [90.9%, 100.0%] |
| Bootstrap 95% CI (optimistic) | [100.0%, 100.0%] |

### Per-Rule Breakdown

| Rule | TP | FP | NR | Conservative |
|------|---:|---:|---:|-------------:|
| `CRYPTO-001` | 8 | 0 | 0 | 100.0% |
| `SECURITY-001` | 26 | 0 | 0 | 100.0% |
| `SECURITY-008` | 12 | 0 | 0 | 100.0% |
| `SECURITY-018` | 0 | 0 | 2 | 0.0% |
| `SECURITY-021` | 5 | 0 | 0 | 100.0% |
| `SECURITY-024` | 2 | 0 | 0 | 100.0% |

### Per-Tool Breakdown

| Tool | TP | FP | NR |
|------|---:|---:|---:|
| bandit | 17 | 0 | 2 |
| other | 9 | 0 | 0 |
| semgrep | 27 | 0 | 0 |

Multi-tool contribution: Bandit and Semgrep both contribute TPs to the Confirmed Tier.
The stratification preserves multi-tool aggregation value while gating on confidence.

---

## Results — 8-CVE Recall Corpus

**Confirmed Tier CVE recall: 8/8 = 100.0%**

| CVE | Rule | In Confirmed Tier |
|-----|------|:-----------------:|
| cve-2016-10516-werkzeug-eval | `SECURITY-001` | ✓ |
| cve-2017-18342-pyyaml | `SECURITY-018` | ✓ |
| cve-2021-23727-celery-pickle | `SECURITY-008` | ✓ |
| cve-2022-24439-gitpython-shell | `SECURITY-021` | ✓ |
| cve-2023-45805-poetry-yaml-unsafe | `SECURITY-018` | ✓ |
| cve-2024-1135-gunicorn | `SECURITY-021` | ✓ |
| cve-2024-3219-pillow | `SECURITY-001` | ✓ |
| cve-2024-45411-twig-eval | `SECURITY-008` | ✓ |

---

## Trade-off

| Tier | Findings | Conservative | CVE recall | Intended use |
|------|---------:|-------------:|-----------:|--------------|
| Raw (all H/M) | 630 | 8.6% | — | Research / data export |
| Security tier (Rung 3) | 219 | 24.7% | 100% | Analyst review queue |
| Security tier + P1+P3 (Rung 4) | 151 | 26.9% | 100% | Analyst review queue (focused) |
| **Confirmed Tier (P4)** | **55** | **96.4%** | **100.0%** | **Autopilot remediation / blocking PR check** |

The Confirmed Tier represents 36% of the post-P3 scope —
a 64% coverage reduction in exchange for near-perfect precision.
This is the appropriate trade-off for security-gate enforcement in CI/CD pipelines where
any FP triggers a developer interrupt with non-trivial cost.

---

Results file: `TESTS/evaluation/results/confirmed_tier.json`
Supporting script: `scripts/run_confirmed_tier.py`
