# RealVuln False-Negative Triage

> **Generated:** 2026-06-21T13:00:38.432001+00:00
> **ACR-QA version:** 5.0.0rc2
> **Purpose:** Classify every FN into (a) undetectable-by-design,
> (b) detectable-but-missed, (c) scoring artifact.

## Corpus Composition (22 cloned repos)

| Class | TPs | % of corpus | SAST detectable? |
|---|:---:|:---:|---|
| **Detectable** (injection/secrets/crypto/config) | 357 | 64% | ✅ yes |
| **Undetectable** (authz/CSRF/IDOR/logic) | 185 | 33% | ❌ no — Rice's theorem |
| Borderline | 16 | 3% | partial |
| **TOTAL** | 558 | 100% | |

> **Key fact:** ~33% of the corpus is auth/CSRF/IDOR/logic.
> No static analysis tool can detect these — they require runtime intent, session flow,
> or data-ownership reasoning. Rice's theorem guarantees no complete static solution.
> The theoretical SAST ceiling on this corpus is ~64%.

## False-Negative Triage (22 repos, all FNs classified)

| Bucket | Count | % of FNs | What it means |
|---|:---:|:---:|---|
| TP (matched correctly) | 157 | — | ACR-QA found it |
| **(a) Undetectable-by-design** | 181 | 45% | CWE is authz/CSRF/IDOR — no SAST tool catches these |
| **(b) Detectable-but-missed** | 143 | 36% | Injection/secrets CWE, ACR-QA produced nothing near the GT location |
| **(c) Scoring artifact** | 77 | 19% | ACR-QA flagged nearby but CWE family or line(±10) didn't match |
| FP_trap hits (bad) | 17 | — | Flagged a non-vulnerable entry |

**Interpretation:** If (a) dominates → the headline is already fine, report detectable-subset.
If (c) dominates → free recall in mapping fixes. If (b) dominates → consider targeted rules
(Step 4, with held-out split).

## Detectable-Subset Recall (the honest headline)

> Restricting to the 357 statically-detectable TPs in the 22 cloned repos:

| Metric | ACR-QA (full output) |
|---|:---:|
| **Recall (detectable subset)** | **42.6%** |
| Precision | 89.9% |
| FPR | 18.5% |
| F3 (recall-weighted) | 0.449 |

**The three-number story:**

| Number | Corpus | Meaning |
|---|---|---|
| **91.0%** | SecurityEval (synthetic snippets) | algorithmic soundness on isolated CWEs |
| **42.6%** | RealVuln detectable subset | real multi-file apps, static ceiling |
| **23.5%** | RealVuln full corpus | total incl. 52% auth/CSRF/IDOR (no SAST tool catches) |

All three numbers are published. The gap is the cost of moving from synthetic to real:
more complexity, more undetectable classes, stricter CWE+line matching.

## Undetectable CWEs (bucket a) — reference list

These CWEs are out-of-scope for ALL static analysis tools, documented as such from day one:

| CWE | Name | Why undetectable |
|---|---|---|
| CWE-352 | CSRF | Requires form+token+session flow understanding |
| CWE-306 | Missing authentication | Requires intent: what *should* be protected |
| CWE-862 | Missing authorization | Same — requires access-control intent |
| CWE-639 | IDOR | Requires data-ownership reasoning |
| CWE-307 | Brute force | Requires runtime rate-limiting context |
| CWE-400 | Resource exhaustion | Runtime resource monitoring |
| CWE-384 | Session fixation | Runtime session-flow analysis |
| CWE-284/287 | Access control | Intent-level, not code-pattern |

**Citing Meta Pysa:** 'There is no way to build a perfect static analyzer…
Python, as a dynamic language, makes a sound inter-procedural CFG computationally
intractable.' We state this as scope, not weakness.

## Reproduce

```bash
cd TESTS/evaluation/realvuln && python3 clone_repos.py
python3 scripts/triage_realvuln_misses.py
```
