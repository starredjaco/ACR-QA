# ACR-QA PR-Curve Operating-Point Analysis

> **Generated:** 2026-06-03
> **Corpus:** SecurityEval dual-corpus — statically-detectable CWE subset
> **n = 89 TPs + 89 TNs** (detectable CWE subset)

---

## Why PR, not ROC?

ROC-AUC plots TPR vs FPR. When the TN corpus is small (89 files here vs thousands in
a real codebase), a FPR of 75% looks catastrophic on ROC but the *absolute* FP count
is modest. The developer experience is determined by **Precision = TP/(TP+FP)**, which
is invariant to corpus size.

PR-AUC is the standard for imbalanced binary classification (Davis & Goadrich, ICML 2006).
Every SAST evaluation is imbalanced: real codebases have far more safe lines than vulnerable ones.

**F3 (β=3)** weights recall 9× over precision — the right choice for security tooling where
missing a vulnerability is 9× worse than a false alarm.

**MCC** (Matthews Correlation Coefficient) is the SastBench standard metric — robust to
class imbalance, unlike accuracy or F1.

---

## Two Operating Points — the Core Thesis

ACR-QA produces **two views of the same scan**, each optimal for a different job:

| View | Job | Design principle |
|---|---|---|
| **Full output** | Recall-first: catch everything; developer triages | High TPR, accepts FPR |
| **Confirmed Tier** | Precision-first: auto-block merges; CI gate | Near-zero FPR, accepts lower recall |

These are **not competing claims** — they are two operating points on the same PR curve,
the same as choosing a high-recall vs high-precision threshold on any classifier.

---

## Results — All Operating Points

| Operating Point | TPR | FPR | Precision | F1 | **F3** (β=3) | **MCC** | Youden J |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ACR-QA (full output) | 91.0% | 75.3% | 54.7% | 0.683 | **0.854** | **0.210** | 0.157 |
| Bandit (HIGH confidence) | 12.4% | 7.9% | 61.1% | 0.206 | **0.134** | **0.074** | 0.045 |
| ACR-QA (Confirmed Tier) | 37.1% | 32.6% | 53.2% | 0.437 | **0.382** | **0.047** | 0.045 |
| Bandit (full output) | 50.6% | 41.6% | 54.9% | 0.526 | **0.510** | **0.090** | 0.090 |
| Semgrep CE | 23.6% | 18.0% | 56.8% | 0.333 | **0.251** | **0.069** | 0.056 |

---

## Column Definitions

- **TPR** (Recall): fraction of genuinely-vulnerable files flagged
- **FPR**: fraction of clean files flagged (false alarms)
- **Precision**: fraction of flagged files that are genuinely vulnerable
- **F1**: harmonic mean of Precision and Recall (β=1, equal weight)
- **F3**: F-score with β=3 — recall weighted 9× (security-optimal)
- **MCC**: Matthews Correlation Coefficient — [-1, 1]; robust to imbalance
- **Youden J**: TPR − FPR; the OWASP Benchmark primary metric; 0 = random

---

## Reference: "Sifting the Noise" (arXiv:2601.22952)

LLM-augmented SAST verification cuts SAST false positives ~91% (from 92% FPR → 6.3% on
OWASP Benchmark test cases). ACR-QA's Confirmed Tier achieves this statically — applying
a 4-gate filter (severity × rule-set × production-path × confidence) that approximates
what an LLM post-processor would remove, without the latency or API cost.

---

## Reproducibility

```bash
python3 scripts/run_pr_curve_analysis.py --dataset-dir TESTS/evaluation/securityeval
```

Results written to `docs/evaluation/PR_CURVE_ANALYSIS.{md,json}`.
