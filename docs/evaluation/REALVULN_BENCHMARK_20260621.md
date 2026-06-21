# ACR-QA RealVuln Benchmark

> **Generated:** 2026-06-21T12:52:56.402974+00:00
> **ACR-QA version:** 5.0.0rc2
> **Corpus:** RealVuln (kolega-ai/Real-Vuln-Benchmark)
> **Repos:** 22/26 cloned (4 GitHub URLs broken in manifest)
> **Methodology:** file + CWE + line (±10) matching; F2/F3 (recall-weighted); MCC

## Why RealVuln

RealVuln uses **real production Python apps** (not synthetic snippets) with hand-labelled
TP and FP traps — designed specifically to resist SAST gaming. Each ground-truth entry
lists `acceptable_cwes` (CWE families that count), `is_vulnerable` (TP vs FP trap),
and file+line location. Scoring requires correct CWE *and* file *and* line (±10).

This directly addresses the 'benchmarked themselves' objection: the corpus is from a
third-party lab, uses real multi-file applications, and includes FP traps.

## Aggregate Results

| Tool | Recall | FPR | F3 | MCC | Youden J |
|------|:---:|:---:|:---:|:---:|:---:|
| **ACR-QA (Bandit + Semgrep + custom)** | **28.1%** | 17.5% | **0.302** | 0.085 | 0.106 |
| Bandit (standalone) | 19.4% | 13.4% | 0.210 | 0.054 | 0.059 |

## Per-Repo Recall (ACR-QA full output)

| Repo | GT TPs | GT FPs | TP | FP | FN | Recall | F3 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| intentionally-vulnerable-python-app | 7 | 2 | 5 | 2 | 2 | 71% | 0.714 |
| vfapi | 9 | 2 | 6 | 0 | 3 | 67% | 0.690 |
| pythonssti | 2 | 1 | 1 | 1 | 1 | 50% | 0.500 |
| damn-vulnerable-flask-application | 15 | 4 | 7 | 1 | 8 | 47% | 0.489 |
| insecure-web | 9 | 2 | 4 | 1 | 5 | 44% | 0.465 |
| vulnerable-flask-app | 21 | 4 | 9 | 0 | 12 | 43% | 0.455 |
| dvblab | 22 | 4 | 9 | 1 | 13 | 41% | 0.433 |
| python-insecure-app | 8 | 2 | 3 | 0 | 5 | 38% | 0.400 |
| vulnpy | 78 | 16 | 28 | 5 | 50 | 36% | 0.381 |
| lets-be-bad-guys | 24 | 4 | 7 | 0 | 17 | 29% | 0.314 |
| dsvpwa | 32 | 6 | 9 | 1 | 23 | 28% | 0.302 |
| djangoat | 50 | 6 | 14 | 0 | 36 | 28% | 0.302 |
| vulnerable-python-apps | 22 | 5 | 6 | 0 | 16 | 27% | 0.294 |
| vulpy | 57 | 6 | 15 | 1 | 42 | 26% | 0.284 |
| dsvw | 27 | 4 | 7 | 2 | 20 | 26% | 0.278 |
| threatbyte | 26 | 5 | 6 | 2 | 20 | 23% | 0.248 |
| vampi | 15 | 4 | 3 | 0 | 12 | 20% | 0.217 |
| extremely-vulnerable-flask-app | 32 | 4 | 5 | 0 | 27 | 16% | 0.171 |
| damn-vulnerable-graphql-application | 36 | 4 | 5 | 0 | 31 | 14% | 0.152 |
| dvpwa | 22 | 4 | 3 | 0 | 19 | 14% | 0.149 |
| flask-xss | 30 | 5 | 4 | 0 | 26 | 13% | 0.146 |
| vulnerable-tornado-app | 14 | 3 | 1 | 0 | 13 | 7% | 0.079 |

## Matching Methodology

A finding is a **TP** if all three match:
1. **File:** finding file path ends-with or equals the GT file path
2. **CWE:** finding CWE is in the GT's `acceptable_cwes` list
3. **Line:** finding line is within ±10 of the GT start_line

A **FP** is a finding that matches a GT entry with `is_vulnerable=false`.
FN = GT TPs that no finding matched. TN = GT FP-traps that no finding matched.

## Reproduce

```bash
# Clone repos (one-time)
cd TESTS/evaluation/realvuln && python3 clone_repos.py

# Run benchmark
python3 scripts/run_realvuln_benchmark.py
```
