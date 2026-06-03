# RealVuln Recall Reconciliation — Execution Plan (do tomorrow)

> **Created:** 2026-06-03 · **Owner:** Ahmed · **Est:** ~1 day
> **Why:** RealVuln full-output recall came back **23.5%** and it *looks* alarming. The diagnosis below
> shows it's mostly a corpus-composition + measurement story, not a detection failure. This plan turns
> the scary number into a precise, defensible breakdown — and recovers the cheap recall that's hiding
> in scoring mismatches. **Do NOT panic-add rules; read the guardrails first.**

---

## The diagnosis (context for tomorrow-you)

RealVuln has **697 vulnerable entries + 120 FP traps**. I split the vuln CWEs by what static analysis
can *physically* detect:

| Bucket | CWEs | ~Count | SAST-detectable? |
|---|---|:---:|---|
| **Injection / secrets** | CWE-79, 80, 89, 94, 798, 259, 321, 312 | ~330 | ✅ yes (taint/pattern/secrets) |
| **Authz / access / CSRF / logic** | CWE-306, 862, 284, 200, 352, 287, 16 | ~364 | ❌ **no — impossible for any SAST** |

**52% of the corpus is authorization/CSRF/IDOR/business-logic** — which needs runtime intent, not
patterns. No tool catches these (Semgrep/Bandit fail them too). **You documented this as out-of-scope
from day one.** So the *theoretical ceiling* for any static tool on RealVuln is **~48%**, and 23.5% of
total ≈ **~48% of the detectable half**. On real code your **FPR also dropped to 15.5%** (vs 75% on
SecurityEval) — that's a *good* precision signal. The RealVuln paper's own best traditional scanner
caught **17.5%**; you're at 23.5%, ahead of it.

**The real story isn't "we're weak." It's "half this corpus is uncatchable by design, and on the
catchable half we lead."** This plan proves that with numbers.

---

## STEP 1 — Triage every miss (do this first; it decides everything)

Categorize all false-negatives into three buckets:
- **(a) undetectable-by-design** — GT CWE ∈ {306, 862, 284, 200, 352, 287, 863, 639, 16, …authz/logic}
- **(b) detectable-but-missed** — GT CWE is injection/secrets but ACR-QA produced nothing near it
- **(c) scoring artifact** — ACR-QA *did* flag that file/line but the CWE-family or line(±10) didn't match

**Action:** add a `--triage` mode to `scripts/run_realvuln_benchmark.py` (or a new
`scripts/triage_realvuln_misses.py`) that, for each FN, records the bucket + (for c) what ACR-QA
*did* report at that location.

**DoD:** `docs/evaluation/REALVULN_TRIAGE.md` with a table: `bucket | count | % of FN | example`.
This single table tells you whether the problem is the corpus (a), the rules (b), or the scoring (c).

---

## STEP 2 — Report recall on the DETECTABLE subset (the honest headline)

This is the exact move you already made and defended with P-1 → P-2.

**Action:**
1. Define `DETECTABLE_CWES` (injection + secrets families) in the benchmark script.
2. Recompute recall / F3 / MCC on the detectable subset only.
3. Rewrite `docs/evaluation/REALVULN_BENCHMARK.md` to lead with **two numbers, both honest**:
   - *Detectable-subset recall* (~the real ~48%, leading Bandit/Semgrep) ← headline
   - *Full-corpus recall 23.5%* ← reported openly, with the "52% is authz/logic, out of SAST scope" line

**DoD:** `REALVULN_BENCHMARK.md` shows both numbers, **explicitly lists the undetectable-by-design
CWEs** and why, and states the ~48% theoretical ceiling. No bare 23.5% without its explanation.

> **Legitimacy — verified, use this in defense (researched 2026-06-03):** subsetting here is NOT
> cherry-picking. RealVuln's *own repo* ships `config/cwe-families.json` + `scorer/metrics.py` that
> group CWEs into scorable families (`sql_injection`, `xss`, `missing_auth`, `broken_access_control`…)
> and the authors state results can be "re-rank[ed] under whatever weighting you prefer." Reporting on
> the detectable families uses the benchmark's *built-in* stratification.
>
> **The examiner objection + rebuttal (memorize):**
> *Objection:* "Excluding 52% to inflate recall to 48% is the Texas Sharpshooter fallacy — drawing the
> target around where you hit."
> *Rebuttal:* "It's an **a priori architectural boundary**, not a post-hoc carve-out. Intent-driven
> authorization (CWE-862) and stateful logic are Turing-undecidable without runtime state (Rice's
> theorem) — evaluating a static taint engine on them measures the *static paradigm's* limit, not this
> tool's. I report the full 23.5% for transparency **and** the 48% architecturally-relevant subset for
> algorithmic comparison — both, always. The subset uses RealVuln's own CWE-family scoring."

---

## STEP 3 — Recover free recall from bucket (c) — scoring/mapping fixes, ZERO new rules

If Step 1 shows many misses are **(c)** — you detected it but the CWE didn't match — that's free recall
sitting in a mapping bug, not a detection gap.

**Action:**
1. Find where canonical rule IDs map to CWE (check `CORE/engines/normalizer.py` / severity_scorer / any
   `cwe` field on findings).
2. For each (c) miss, check if ACR-QA's CWE is a *sibling* of the GT's `acceptable_cwes` (e.g. you said
   CWE-79, GT wanted CWE-80 — same XSS family). Widen the canonical→CWE map or the family-matching.
3. Re-run the benchmark.

**DoD:** recall rises from mapping fixes *alone*, with no new detection rules and no FPR increase.
Document the before/after in `REALVULN_BENCHMARK.md`.

---

## STEP 4 — (Optional, careful) Close genuine detectable gaps from bucket (b)

Only for **injection/secrets** CWEs that were genuinely missed (e.g. a Flask/Django-specific sink the
taint rules don't know).

**Action:** add targeted taint sinks/rules in `config/taint_sinks.yml` or `TOOLS/semgrep/python-rules.yml`,
**each with a test**, validated on a **held-out split** (tune on half the repos, measure on the other half)
so you're not overfitting to RealVuln the way 91% overfit to SecurityEval.

**DoD:** detectable-subset recall improves; FPR stays ≤ ~16%; every new rule has a passing test;
held-out split reported so the gain is generalization, not memorization.

> **Skip this step entirely if Steps 1–3 already land detectable-subset recall in a defensible range.**
> Adding rules is the lowest-priority, highest-risk move here.

---

## STEP 4b — (Recommended, SAFE) Recover framework-structural authz/CSRF detections

Researched 2026-06-03: a chunk of the "undetectable" 364 is actually **structurally** detectable with
framework-aware rules — *structural absence* (no decorator present), not *intent inference*. Competitors
ship these (Semgrep's framework-native Django/Flask/FastAPI analysis runs at ~84% TP). This is **legit
recall, no FP explosion** — the opposite of the IDOR trap.

**Targets — ranked by FP-safety (researched 2026-06-03, do them in this order):**
1. **`DEBUG=True` / insecure config (CWE-16) — DO THIS, near-zero FP.** Pure AST assignment match.
   Existing rule: `python.django.security.audit.debug-true`; Flask `app.run(debug=True)`. Only caveat:
   dev-vs-prod settings files — exclude obvious dev configs.
2. **`@csrf_exempt` / disabled CSRF (CWE-352) — DO, but GATE it (moderate FP).** Existing:
   `python.django.security.audit.csrf-exempt`; Flask-WTF `WTF_CSRF_CHECK_DEFAULT=False`. Real FP source:
   legitimate webhook/API endpoints that use HMAC instead of CSRF tokens — surface as "review", not "high".
3. **Missing auth decorator (CWE-306) — ⚠️ CAUTION, HIGH FP. Only if the app uses imperative decorators.**
   Negative-pattern match (`@app.route` present, `@login_required`-class absent) generates a *massive* FP
   rate when auth is delegated to middleware / API gateway / base-class — the route looks bare but is
   protected, and static analysis can't see the middleware. **Gate hard or skip unless triage (Step 1)
   shows the target apps use route-level decorators.**

**Action:** add as framework-aware rules in `TOOLS/semgrep/python-rules.yml` (or new
`python-framework-rules.yml`), each with a test, validated on the **held-out split**. Semgrep logic for
"absence": `pattern` (the route) + `pattern-not` (route + required decorator).

**DoD:** CWE-16 + gated CWE-352 move from "undetectable" to detected; **FPR stays ≤ ~16%**; every rule has
a passing test; gain reported held-out. CWE-306 only if it doesn't blow the FPR.

> **Hard line:** Step 4b is *structural-absence* detection only. The moment a rule needs to know "should
> THIS resource be scoped to THIS user" (ownership/IDOR), it belongs in Future Work below — not here.

---

## FUTURE WORK (thesis chapter, NOT a pre-defense build) — LLM-hybrid IDOR / ownership authz

The genuine hard core — IDOR (CWE-862/639), business-logic authorization — is **semantic, not
structural**: a tool can't infer `Order.user_id == user.id` is mandatory without the app's domain model.
The 2025/26 frontier is **LLM-hybrid** (static traces the data path → LLM judges if the missing check is
a real bug), and it *does* find IDORs pattern-matching misses — but at **23–65% precision** (NDSS 2025),
i.e. a false-positive factory if ungated.

**Why this is Future Work, not a pre-defense feature:**
1. 23–65% precision reintroduces the exact noise problem the Confirmed Tier exists to kill.
2. An IDOR finding **can't be exploit-verified** generically — it breaks the "every finding is *proven*"
   thesis spine.
3. Scope-creep 3 weeks before defense.

**What to actually write (the 10/10 rigor move):** a thesis section that (a) draws the line — "provable
static detection ends at semantic authorization"; (b) cites the frontier with **verified** sources; (c)
optionally ships a *tiny, hard-gated* PoC behind the Confirmed Tier, labelled experimental. Drawing the
line knowingly beats faking the number.

**Verified citations for this section (web-checked 2026-06-03):**
- **Standalone LLM ≈ 23–65% precision** on IDOR/logic → *"From Large to Mammoth"*, Lin & Mohaisen (UCF),
  **NDSS 2025** (ndss-symposium.org). The honest baseline showing naïve LLM = FP factory.
- **IDOR/BAC is solved DYNAMICALLY, not statically** → **BACScan**, CCS 2025 (CUHK, DOI
  10.1145/3719027.3744825, 35 CVEs assigned) and **EvoCrawl**, NDSS 2025 — both black-box/runtime, hitting
  90–100% precision. *This is the strongest argument that authz belongs to the dynamic/exploit-verified
  side of your architecture, not the static side — it aligns IDOR with your exploit-verification thesis
  as future work, not a static-rule gap.*

**DoD (optional):** a `## Future Work: Semantic Authorization` section in the thesis + QA_PREP answer:
*"Static analysis ends at intent. Structural authz I detect; ownership-logic IDOR needs LLM-hybrid at
23–65% precision, which I scope as future work rather than ship as noise."*

---

## STEP 5 — Update the defense narrative (½ hour, high leverage)

**Action:** in `README.md` and `docs/QA_PREP.md`, add the three-number framing as *deliberate measurements*:

| Number | Corpus | What it measures |
|---|---|---|
| 91% | SecurityEval detectable subset | algorithmic soundness on isolated CWEs |
| ~48% | RealVuln **detectable** subset | real multi-file apps, the hard honest number — leads Bandit/Semgrep |
| 23.5% | RealVuln full | total recall incl. the 52% authz/logic that no SAST can reach |

Add the QA_PREP answer to **"Why is RealVuln recall only 23.5%?"** → the 52%-uncatchable / ~48%-ceiling
/ leads-the-baselines story.

**DoD:** QA_PREP has a crisp, memorized answer; README never shows a bare number without its corpus.

---

## Guardrails (the way to NOT get cooked)

1. **Never add a rule to "detect" CWE-306/862/284/352/287 (authz/CSRF/IDOR).** You cannot pattern-match
   missing authorization — you'd only manufacture false positives. Claiming you detect these is the one
   thing that *would* sink the defense. Honesty about the limit beats a fake number.
2. **Detectable subset is not cheating** — it's standard SAST-eval methodology, and you already defended
   it once (P-2). Always report the full number alongside it.
3. **Any new rule (Step 4) is validated on a held-out split.** No tuning on the same repos you score on.
4. **Tests green before commit** (ruff format + ruff check + mypy CORE/ + pytest). Push at end.

---

## Order of operations tomorrow

```
1. Step 1  triage script        → REALVULN_TRIAGE.md  (the a/b/c split)
2. Read the split. If mostly (a)+(c): you're already fine — Steps 2+3+5, done by lunch.
3. Step 2  detectable-subset report
4. Step 3  mapping fixes (free recall, zero new rules)
5. Step 4b framework-structural authz/CSRF recovery (SAFE, held-out split)  ← real recall
6. Step 5  narrative (README + QA_PREP) + Future-Work line
7. Step 4  ONLY if detectable recall still weak, held-out split
8. ruff + mypy + pytest → commit → push
   (LLM-hybrid IDOR = Future Work chapter, NOT today)
```

**Expected outcome:** the headline becomes "~48% recall on real apps (detectable subset), leading
Bandit & Semgrep, with the full 23.5% reported honestly and the 52%-uncatchable explained" — a number
that *survives* the skeptic instead of feeding them.
