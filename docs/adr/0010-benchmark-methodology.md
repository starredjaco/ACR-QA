# ADR 0010 — Benchmark Methodology: SecurityEval Dual-Corpus, PR-AUC not ROC

**Status:** Accepted
**Date:** 2026-06-03
**Author:** Ahmed Mahmoud Abbas

---

## Context

ACR-QA reports multiple evaluation metrics. This ADR explains the corpus and metric choices.

## Decision

**Primary corpus:** SecurityEval (s2e-lab/SecurityEval, NeurIPS-cited).
- TPs: `Testcases_Insecure_Code/` (89 files, statically-detectable CWEs, each genuinely vulnerable)
- TNs: `Testcases_Copilot/` (89 files, Copilot's security-conscious completions — should NOT fire)

**Primary metric:** Youden J = TPR − FPR (OWASP Benchmark standard).
**Secondary metrics reported:** Precision, Recall, F1, F3 (β=3, recall-weighted), MCC.

**Why PR-AUC is reported instead of ROC-AUC:**
ROC-AUC uses FPR = FP/(FP+TN). With only 89 TNs (the SecurityEval Copilot corpus), a 75.3% FPR
looks bad on ROC. But on a real 10 KLOC production codebase with tens of thousands of clean files,
the absolute FP count is small. Precision = TP/(TP+FP) is immune to corpus size — it reflects
the true developer experience (how noisy is my alert queue?). Reference: Davis & Goadrich, ICML
2006; SastBench (arXiv:2601.02941).

**Why F3 (β=3)?** Security literature recognizes the cost asymmetry: a missed vulnerability (FN)
costs orders of magnitude more than a false alarm (FP). F3 weights recall 9× over precision,
reflecting the security practitioner's preference. Compare: Bandit uses severity tiers for the
same reason.

**P-1 retraction:** the original P-1 benchmark (file-level precision on `Testcases_Copilot/`) was
retracted because it scored correct silence on safe code as missed detections. The P-2 and OWASP-
methodology benchmarks use only `Testcases_Insecure_Code/` as TPs, correcting this error.
See `docs/evaluation/RECONCILIATION.md`.

## Consequences

- **Positive:** methodology matches published benchmarks (OWASP, SastBench). Examiners recognize it.
- **Negative:** SecurityEval is a generative-LLM benchmark — files are single-function snippets,
  not multi-file applications. Real-world recall may differ. We disclose this limitation in §5.8.
