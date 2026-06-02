# P-1 Benchmark Pre-Registration — ACR-QA vs Bandit vs Semgrep CE

> **Pre-registered:** 2026-06-02 (before any runs)
> **Registered by:** Ahmed Mahmoud Abbas
> **Script:** `scripts/run_benchmark_p1.py`
> **Status:** Methodology locked. Results published after first run.

---

## 1. Research Question

Does ACR-QA's Confirmed Tier (96.4% precision gate) outperform standalone Bandit and Semgrep CE
on the SecurityEval AI-code benchmark at equal or better recall, on a corpus ACR-QA has never seen?

---

## 2. Dataset

**SecurityEval** (Siddiq & Santos, 2022)
- 130 Python code samples, each containing one CWE-labeled vulnerability
- Sourced from GitHub Copilot prompts — directly relevant to the AI-code problem
- Ground truth: CWE labels assigned by the dataset authors (not ACR-QA)
- URL: https://github.com/s2e-lab/SecurityEval
- Commit pinned at run time (recorded in JSON output)

**Inclusion criteria:** All 130 Python samples.
**Exclusion criteria:** None.

---

## 3. Tools & Versions

| Tool | Version at run | Config |
|------|---------------|--------|
| ACR-QA | recorded at run | Confirmed Tier only (`--no-ai --json`) |
| Bandit | recorded at run | Default rules, `-r`, JSON output |
| Semgrep CE | recorded at run | `--config=p/python` |

All tools run on the same files, same commit, same machine, same Python environment.

---

## 4. Metric Definitions

- **TP (True Positive):** Tool found a finding in a file that has a CWE label.
- **FP (False Positive):** Tool found a finding in a file that has no CWE label.
- **FN (False Negative):** Tool found no finding in a CWE-labeled file.
- **Precision:** TP / (TP + FP) — file-level matching.
- **Recall:** TP / (TP + FN) — file-level matching.
- **F1:** 2 × Precision × Recall / (Precision + Recall).
- **Confidence intervals:** Wilson score interval at 95%.

File-level matching is conservative (same as Endor Labs' published methodology).

---

## 5. Hypotheses (pre-registered)

**H1:** ACR-QA Confirmed Tier precision > Bandit precision (at file-level).
**H2:** ACR-QA Confirmed Tier precision > Semgrep CE precision.
**H3:** ACR-QA Confirmed Tier recall ≥ Bandit recall.

**Kill criterion:** If H1 AND H2 are both false, the Confirmed Tier precision claim is not
supported on this corpus → revise the claim in positioning materials.

---

## 6. Expected Results (before running)

Based on prior 30-repo internal benchmark (v5.0.0):
- ACR-QA Confirmed Tier: ~96% precision, ~40% recall (by design — trades recall for trust)
- Bandit: ~15-25% precision, ~12-15% recall
- Semgrep CE: ~35-45% precision, ~60-70% recall

The Confirmed Tier is NOT expected to win on recall — that is by design.
It is expected to win clearly on precision.

---

## 7. Limitations

- File-level matching overestimates precision for tools with many findings per file.
- SecurityEval uses AI-generated code; results may not generalize to all codebases.
- ACR-QA was not trained on SecurityEval but shares rule overlap with public CWE patterns.
- Bandit and Semgrep also target overlapping CWE categories.

---

## 8. Reproducibility

```bash
# Step 1: clone dataset (one-time)
git clone https://github.com/s2e-lab/SecurityEval TESTS/evaluation/securityeval

# Step 2: run benchmark (records tool versions + commit hash in JSON output)
python3 scripts/run_benchmark_p1.py --dataset-dir TESTS/evaluation/securityeval

# Step 3: results in docs/evaluation/P1_BENCHMARK_<date>.md + .json
```

Results are deterministic given the same tool versions and dataset commit.
