# Prototype — LLM-Augmented Detection (Phase 0 result)

> **Generated:** 2026-06-03 · Phase 0 of `docs/GO_BIG_LLM_DETECTION_PLAN.md`
> **Model:** llama-3.3-70b-versatile (zero-shot, **single-file**, no cross-file context)
> **Corpus:** RealVuln repos (vampi, dsvpwa, flask-xss); scored vs ground truth (file+CWE+line±10)

## Result — three strictness levels (the diagnostic)

| Repo | strict (file+CWE+line) | file+line (ignore CWE) | file-only | false-alarm rate |
|---|:---:|:---:|:---:|:---:|
| vampi | 33% | 60% | 100% | ~80% |
| dsvpwa | 9% | 41% | 62% | ~83% |
| flask-xss | 20% | — | — | ~78% |
| **aggregate** | **~17%** | **~50%** | **~75%** | **~80%** |

Rule-based baseline for reference: **25.1% full / 37.8% detectable**.

## What this means (honest)

1. **The LLM is NOT detection-blind.** It localizes the vulnerable *file* 62–100% of the time. The low
   strict-recall is mostly **CWE mislabeling + line drift**, not failure to notice the bug.
2. **At file+line (~50%) it is competitive with / above the rule-based detectable subset (37.8%).** There
   is genuine recall potential here.
3. **But the false-alarm rate is ~80%** — the classic standalone-LLM precision collapse (cf. NDSS 2025,
   23–65% precision). Ungated, this is unusable.
4. **This is the hybrid thesis in miniature:** LLM supplies recall, *something* must supply precision.
   ACR-QA's exploit-verifier is that something — but only for the ~10 exploitable categories; secrets/
   crypto/config would need the LLM-jury (`second_opinion`) instead.

## Verdict: NO-GO as a pre-defense shipped feature · STRONG Future Work

- **Ungated LLM detection is worse than rules** (17% strict, 80% FP) — do **not** ship it as-is.
- **The gated hybrid is promising but a multi-week build** (better localization + CWE mapping + cross-file
  context + exploit-gating + jury for non-exploitable classes). Too risky to finish safely before Jun 25.
- **Best move:** make it a **Future Work chapter backed by this prototype's real numbers** — "preliminary
  LLM detection reaches 50–75% file-level recall at 80% false-alarm rate, motivating an exploit-gated
  hybrid." That is a stronger, more honest research contribution than a half-built feature.

## If pursued post-defense (the real "go big")

1. Cross-file/agentic context (not single-file zero-shot — the #1 handicap here).
2. CWE normalization: map LLM CWE output → RealVuln families (recovers the 17%→50% gap).
3. Exploit-gating for the 10 verifiable categories + calibrated LLM-jury for the rest.
4. Held-out split; report PR curve (LLM-augmented full output vs exploit-gated Confirmed Tier).

**Reproduce:** `python3 scripts/proto_llm_detection.py --repos realvuln-vampi realvuln-dsvpwa`
