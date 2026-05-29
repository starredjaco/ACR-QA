# T4.2 Bootstrap Confidence Intervals

_Generated: 2026-05-29 17:31 UTC_
_Method: Per-repo bootstrap resampling. Unit of resampling = repo. Each iteration draws N repos with replacement, sums TP/FP/NR, computes precision. 95% CI = 2.5th–97.5th percentile of 10,000 samples._
_n_boot = 10,000, n_repos = 30_

## Summary

| Metric | Point Estimate | 95% CI | CI Width | n repos |
|--------|---------------|--------|----------|---------|
| H/M all-tools, conservative | **8.6%** | [4.5%, 13.9%] | 9.4% | 30 |
| H/M all-tools, optimistic | **28.1%** | [19.6%, 36.6%] | 17.0% | 30 |
| Security-tier, conservative | **24.7%** | [14.6%, 35.4%] | 20.8% | 30 |
| Security-tier, optimistic | **37.9%** | [26.4%, 50.4%] | 24.1% | 30 |
| H/M Python only, conservative | **5.9%** | [2.9%, 9.3%] | 6.3% | 25 |
| H/M JavaScript only, conservative | **18.5%** | [4.1%, 41.2%] | 37.1% | 5 |
| Sec-tier Python only, conservative | **16.8%** | [9.1%, 26.1%] | 17.0% | 25 |
| Sec-tier JS only, conservative | **54.4%** | [45.8%, 66.7%] | 20.8% | 5 |

> **Conservative**: NEEDS_REVIEW → FP.  **Optimistic**: NEEDS_REVIEW → TP.

## Interpretation

### Primary defence number

Security-tier precision: **24.7% [14.6%, 35.4%]** (conservative) / **37.9% [26.4%, 50.4%]** (optimistic).

The 95% confidence interval captures uncertainty arising from the particular
set of repositories in the corpus. If we had sampled a different set of 24
production Python/JS libraries, precision would likely fall within this range.

### H/M blended precision

All-findings H/M precision: **8.6% [4.5%, 13.9%]** (conservative). The wider CI here reflects high variance across repos — some repos generate many low-precision quality findings (radon/vulture) while others are security-heavy.

### Language breakdown

- Python (sec-tier): 16.8% [9.1%, 26.1%] conservative
- JavaScript (sec-tier): 54.4% [45.8%, 66.7%] conservative

JS sec-tier CI is wider (fewer repos) — interpret with more caution.

### CI width interpretation

Security-tier CI width: 20.8% —
a ±10.4pp range. This is expected for a 24-repo precision corpus;
a corpus of 100+ repos would narrow this to under ±5pp.

## Bootstrap Distribution Statistics

| Metric | Mean | Std Dev | CI Width |
|--------|------|---------|---------|
| Security-tier, conservative | 24.8% | ±5.3% | 20.8% |
| Security-tier, optimistic | 38.0% | ±6.2% | 24.1% |
| H/M all-tools, conservative | 8.7% | ±2.4% | 9.4% |

## Summary for Defence

**Q: How reliable are your precision numbers?**

The 95% bootstrap CI for security-tier precision is [14.6%, 35.4%] (conservative) / [26.4%, 50.4%] (optimistic). These CIs are computed by per-repo bootstrap resampling over 30 production repositories with 10,000 iterations. The interval captures corpus-sampling uncertainty — if we re-ran the benchmark on a different set of production libraries, we would expect precision to fall in this range with 95% probability.
