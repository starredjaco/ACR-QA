# Go Big — LLM-Augmented Detection, Exploit-Gated (the "best of the bests" bet)

> **Created:** 2026-06-03 · **Owner:** Ahmed + agent · **Status:** ✅✅ **PHASE 1+2 SHIPPED & VALIDATED (held-out GO)**
> **Held-out result (commit 6498a78, `docs/evaluation/LLM_AUGMENTED_BENCHMARK_held_out_20260603.md`):**
> RULES 27.2%/91.3% → **UNION-GATED 32.4% recall / 89.5% precision (+5.2pp recall, precision held)** on 16
> held-out repos (no overfitting). `CORE/engines/llm_detector.py` (detect + second-opinion gate) +
> `run_llm_augmented_benchmark.py` (4 operating points). Passed its own decision gate. **The go-big bet paid
> off — real, modest, honest, held-out.** Remaining: full-corpus re-run + wire into live pipeline + README/QA_PREP.
> **Phase 0 result (`docs/evaluation/PROTO_LLM_DETECTION.md`):** LLM-alone is below rules, BUT the **union
> (rules ∪ LLM) beats rules-alone by +8.9pp recall, stable across 6 repos** — they're complementary. The
> LLM half is 80–90% false alarms, so the bet hinges on gating keeping precision. **Decision: GO on the
> SCOPED hybrid (LLM-detect → gate through existing `second_opinion`/`confirmed_tier`/exploit-verifier),
> achievable in days. NOT the months-long SOTA agentic rebuild.** Realistic outcome: detectable recall
> ~37.8% → ~45% + a novel gated-hybrid contribution. **Kill-switch:** if gating can't hold precision, revert
> to Future Work. Next experiment = the gating-precision test (Phase 2 below, pulled forward).
> **Thesis line:** *"The only tool that detects aggressively with an LLM **and** proves every finding by
> exploitation — so it competes on recall without paying the LLM false-positive tax."*

---

## The bet (why this can actually reach the top tier)

On RealVuln, the tiers are: rule-based SAST **17–19%** · raw LLMs **~50%** · security-specialized
**73–80%**. ACR-QA is at **25.1% full / 37.8% detectable** — leading the rule-based tier because
**detection is still pure rule-based** (Bandit/Semgrep/taint). The LLM only triages/explains today.

The higher tiers got there with **LLM detection** — but they're capped at **23–65% precision** (NDSS
2025) because a raw LLM hallucinates vulns and they have **no way to filter**.

**ACR-QA's unfair advantage:** a 10-category **exploit-verifier**. So we can do the thing nobody else
can do safely:

> **LLM detects aggressively (recall ↑) → exploit-verifier kills hallucinations (precision held).**

That is on-thesis, not a distraction — it's *exploit-verification applied to detection*. If it works,
the headline becomes "competes with security-specialized recall **and** every finding is exploit-proven."

---

## The disciplined rule: PROTOTYPE before committing

3 weeks to defense. Half-shipping a big feature is worse than not shipping it. So we **prove the lift
with data first**, then decide:

- **GO** if prototype shows detectable recall **37.8% → 55%+** with precision/FPR held → build it for real, new headline.
- **NO-GO** → it becomes the killer *Future Work* chapter; defend on the solid current numbers. Either way we win, because the decision is data-driven.

---

## Phase 0 — PROTOTYPE (today, agent, god mode)

**Goal:** one number — does LLM detection lift RealVuln recall, and what does it do to FPR?

**Design (decoupled from Docker for speed):** RealVuln scoring is static ground-truth matching
(file + CWE-family + line±10), so to measure *can the LLM find more*, we don't need exploitation —
we need LLM candidates scored against GT. Exploit-gating is the production precision story (Phase 2);
the prototype measures raw LLM detection lift + its FPR on the 120 traps (which tells us how much
gating we'll need).

**Build:** `scripts/proto_llm_detection.py`
1. For 3–4 RealVuln repos (small ones first), read each Python file.
2. Prompt the LLM (reuse `explainer.py` Groq client) → return candidate findings as JSON
   `[{file, line, cwe, severity, why}]`. Detection prompt, not explanation.
3. Score candidates vs ground truth with the existing matcher (file + CWE-family + line±10).
4. Report three recalls — **rule-based / LLM-only / union** — plus **FPR on the 120 traps** for each.

**DoD:** `docs/evaluation/PROTO_LLM_DETECTION.md` with the 3-way recall + FPR table on the sampled repos.
**Decision gate:** union recall meaningfully > rule-based AND LLM FPR is gate-able (not catastrophic).

---

## Phase 1 — LLM detection pass (only if Phase 0 says GO) ~3–4 days

- `CORE/engines/llm_detector.py` — multi-file-aware Python detection; chunking + cross-file context;
  emits `CanonicalFinding`s tagged `source="llm"`, `confidence` per finding.
- Wire into the pipeline as an *additive* detection source (never replaces rules).
- Held-out split: tune prompts on half the RealVuln repos, measure on the other half. No overfitting.

**DoD:** detectable-subset recall up, on the held-out half, reported honestly.

---

## Phase 2 — Exploit-gating for precision (the differentiator) ~2–3 days

- LLM candidates flow into `exploit_verifier` (10 categories) + Confirmed Tier.
- Three tiers emerge: `llm-candidate` (recall view) → `confirmed` (exploit-verified, near-0 FP).
- The headline metric: **high union recall (full output) + near-0-FP Confirmed Tier**, on one PR curve.

**DoD:** PR curve showing LLM-augmented output dominates rule-based at every operating point; Confirmed
Tier precision held ≥90%.

---

## Phase 3 — Re-benchmark + narrative ~1 day

- Re-run RealVuln + SecurityEval with the LLM-augmented pipeline; update all eval docs + README + QA_PREP.
- Honest framing: report the lift, the held-out methodology, and the exploit-gating that keeps precision.

---

## Guardrails

1. **Prototype gates the whole thing.** No Phase 1+ until Phase 0 shows a real, measured lift.
2. **LLM detection is additive** — never removes rule-based findings; the trustworthy core stays.
3. **Held-out split always** — tune and measure on different repos, or it's overfitting theater.
4. **Exploit-gating is the precision story** — never ship raw LLM findings as high-confidence.
5. **Watch Groq rate limits + latency** — if scans blow past minutes, that's a real product cost to report.
6. **If it slips, it's Future Work** — defend on 25.1%/37.8%, which is already honest and field-leading-for-tier.

---

## Optional deep-research (for Phase 1 prompt optimization, NOT blocking the prototype)

Only worth running *if Phase 0 shows GO*, to avoid reinventing prompt/context design. Prompt at the
bottom of this session. The prototype starts now without it.
