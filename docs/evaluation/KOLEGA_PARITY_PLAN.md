# Plan: Match & Beat kolega-enterprise — Phased Detector Roadmap

> **Goal:** make ACR-QA's deterministic engine match or beat kolega-enterprise's detection
> *coverage* on a **held-out** basis, then win decisively on the axes kolega can't touch
> (free, deterministic, reproducible, auditable). Status as of 2026-06-22.

---

## ⭐ Execution roadmap (definitive order — do them in THIS sequence)

Ordered by (competitive advantage × feasibility), respecting dependencies. All numbers below are
**official-scorer verified** (2026-06-22): full corpus **53.8% R / 47.3% P / F2 52.3%**, held-out
**51.2% R / 47.2% P**, confirmed-tier **78.6% P**. ACR-QA already beats Opus 4.8 (51.7%) & Gemini
3.1 (52.6%) on mean recall, tied with Sonnet 4.6 (53.9%); only GPT-5.5 (58.2%) leads.

| # | Phase | Why this slot | Effort | Payoff | Status |
|---|-------|---------------|--------|--------|--------|
| ✅ | **Auth/IDOR/CSRF detectors** (was Ph 0/2) | biggest combined-pipeline gap | done | held-out 46→51% | **DONE** |
| ✅ | **Confirmed Tier** (cross-detector agreement) | answers the #1 weakness (47% precision); proven 78.6% | ★ low | high-precision MODE + credibility | **DONE** — tiered output shipped + unit-tested |
| 🟡 | **Exploit-verification PROVEN tier** | engine real + ran (Docker); but RealVuln repos are libraries / apps needing manual DB+env setup, so **auto-detonation = 0/53 on this benchmark**. It's a PRODUCTION feature (verifies findings in a *deployed* app), NOT a static-benchmark tier — honest re-scope. | ★★★ | production differentiator | **ran 2026-06-23; 0 detonated (benchmark mismatch)** |
| 🟡 | **Ensemble expansion** (high-prec Bandit subset done; Semgrep registry needs network) | corroboration source grew Confirmed tier 44→75 TP @ 80.6% | ★★ low-med | +Confirmed precision | **Bandit-corroboration DONE**; registry pending network |
| 🟡 | **External held-out corpus** | the *unfakeable* proof we generalize | ★★ low-med | believable generalization | **PyGoat DONE** (48.1% R external, codeload bypass); more repos pending |
| **5** | **JS + cross-file taint** (DOM XSS, Python→template) | recall lever for when the easy ones are exhausted (diminishing) | ★★★ med | +2–4pp recall | when recall stalls |
| ❌ | **Cheap-LLM precision filter** (`scripts/llm_precision_filter.py`) | TESTED & REJECTED — cheap/mid Groq models (8b, 70b) can't do exploitability reasoning in one pass; net-neutral-to-negative on F2 (53.8→53.5%), drops real vulns. Frontier agents are precise via expensive multi-step tool use, not a classify call. | ★★ | — | **tested-negative**, opt-in only |
| ⏸ | **Precise per-sink taint** (was Ph 1) | net-negative in combined pipeline (Semgrep overlaps); only for a Semgrep-free engine | — | AST-only mode | deprioritised |

**One-line rationale:** lock in the high-precision tier (1) → build the exploit-proven moat (2) → grow
recall cheaply (3) → make the claim unfakeable (4) → squeeze remaining recall (5) → optionally chase
top-F2 with an opt-in LLM filter (6). Detailed phase write-ups below (original numbering retained).

> **FINAL roadmap status (2026-06-23) — all 10 phases resolved:**
> Phase 0 ✅ (auth/IDOR/CSRF, held-out 46→51%) · Phase 1 ⏸ tested-negative (generic taint, opt-in) ·
> Phase 2 🟡 (sensitive-route + IDOR owner-absence done; deeper authz left — diminishing) ·
> Phase 3 ✅ (JS DOM-XSS) · Phase 4 ✅ (confidence tiers) · Phase 5 ✅ (Confirmed tier 80.6%) ·
> Phase 6 🟡 (Bandit-corroboration ✅; registry packs tested-negative) · Phase 7 🟡 (exploit engine
> ran; 0 auto-detonated on this benchmark — production-only) · Phase 8 ❌ tested-negative (LLM filter) ·
> Phase 9 🟡 (PyGoat external 48.1% ✅; more repos blocked by dead URLs).
>
> **FIVE "clever shortcuts" tested net-negative:** Semgrep registry packs, generic inter-procedural
> taint, Bandit-all (vs corroboration), cheap-LLM precision filter, and call-graph reachability
> pruning. Each dropped real vulns because imperfect whole-program analysis is worse than no analysis.
> **The consistent, repeatedly-verified lesson:** this deterministic engine is at a genuine ceiling
> (~53% recall / ~47% precision / Confirmed-tier 80.6%); only *targeted* detectors (auth/IDOR/CSRF)
> and *corroboration-based* confidence move it. That negative-result discipline — testing and
> honestly rejecting five plausible ideas — is itself the most valuable result here.

---

## 0. The honest premise (read first)

kolega-enterprise scores **95% recall / 76% precision** on RealVuln — but it is the **benchmark
author's own tool**, with **247 distinct detectors**, tuned on these exact 22 repos (rule names
literally carry iteration markers: `r2`, `h3`, `strict`). Most of those 247 are long-tail (1–2
findings, overfit to one repo). **We will not — and should not — chase the 95%**; replicating
per-repo overfit fails our held-out test and is dishonest.

**What we steal instead:** the ~40 *general* detection strategies that carry kolega's recall, each
validated on our DEV/UNSEEN split. Current honest standing: **48.3% held-out recall / 48.3%
precision** (already #1 vs all traditional SAST). Realistic honest ceiling with this plan:
**~60–65% held-out recall at ~55–65% precision** — which would beat the *typical* recall of every
frontier LLM (GPT-5.5 ~57%) while staying deterministic and free. That is the real prize.

### How kolega actually reaches its numbers (reverse-engineered)

1. **Per-sink precise taint**, not one generic pass — `sql_taint_flow` (86% prec),
   `path_taint_wrapper_peel` (67%), `ssrf_taint_flow` (71%) are *separate* detectors with
   sanitizer awareness. (Our generic inter-procedural attempt collapsed precision — this is why.)
2. **Recall is the sum of ~40 precise detectors**, not one magic rule. ~20 of them are 100%-precision
   and add a few TPs each.
3. **It accepts low precision on auth for recall** — `missing_auth_strict_authz_aware` (its #1, 55
   TP) runs at **53% precision**; `auth_endpoint` at 43%. F2/F3 weight recall, so this trade pays.
4. **It has a confidence-tier system** — the `certain:` prefix marks high-confidence findings
   (= ACR-QA's existing "Confirmed Tier" concept). Enables a high-precision mode on top of high recall.
5. **Multi-file-type** — scans py + html + jinja2 + **js** + yml + xml + php.

---

## 1. Detector inventory (top ~40 by TP contribution)

Status: ✅ have · 🟡 partial/weak · ❌ missing. "TP/tot" = kolega's recall/precision on RealVuln.

| kolega detector | CWE | TP/tot | prec | ACR-QA status | Phase |
|-----------------|-----|--------|------|---------------|-------|
| missing_auth_strict_authz_aware | 306 | 55/104 | 53% | 🟡 sensitive-route heuristic | **2** |
| sql_taint_flow | 89 | 38/44 | 86% | 🟡 f-string/format only | **1** |
| path_taint_wrapper_peel | 22 | 22/33 | 67% | 🟡 1-level wrapper | **1** |
| ssrf_taint_flow | 918 | 22/31 | 71% | 🟡 wrapper/urllib | **1** |
| auth_endpoint (login rate-limit) | 307 | 20/46 | 43% | 🟡 basic CWE-307 | **2** |
| safe_filter | 79 | 19/22 | 86% | ✅ | — |
| session_auth_no_csrf | 352 | 18/28 | 64% | ✅ added | — |
| redos_regex_sink | 1333 | 17/17 | 100% | ✅ | — |
| assignment_secret_literal | 200/798 | 15/15 | 100% | ✅ | — |
| idor_r2_strict_owner_absence | 639/200 | 14/17 | 82% | 🟡 weak IDOR | **2** |
| config_subscript_secret_literal | 798 | 12/13 | 92% | ✅ | — |
| weak_md5_security_hash | 327/256 | 11/13 | 85% | ✅ gated | — |
| codeexec_ast_taint | 94 | 10/12 | 83% | 🟡 eval/exec | **1** |
| run_debug_true | 215 | 10/10 | 100% | ✅ | — |
| python_response_concat | 79 | 9/12 | 75% | ✅ taint-gated | — |
| deser_pickle / deser_yaml | 502 | 14/18 | ~80% | ✅ broadened | — |
| csrf_exempt | 352 | 8/11 | 73% | ❌ | **0** |
| ssti_template_construction | 94/1336 | 7/8 | 88% | ✅ | — |
| return_error_detail / direct_print | 209 | 14/25 | ~55% | ✅ added | — |
| python_response_augassign_direct | 79 | 7/11 | 64% | ✅ added (benchmark-neutral) | — |
| autoescape_false | 16/79 | 7/15 | 47% | ✅ | — |
| ccac_client_literal_gate | 16 | 6/6 | 100% | ❌ (verify=False client gate) | **0** |
| sqlite_trace | 532 | 6/6 | 100% | ❌ | **0** |
| attribute_secret_literal | 798 | 5/5 | 100% | 🟡 self.x='secret' | **0** |
| template_var_js_attr | 79 | 5/5 | 100% | ❌ (JS-context template var) | **3** |
| js_tainted_dom_sink | 79 | 5/5 | 100% | ❌ (no JS scanning) | **3** |
| template_form | 352 | 5/5 | 100% | 🟡 POST form no-csrf | **0** |
| tainted_subprocess_shell_true | 78 | 5/5 | 100% | ✅ | — |
| certain:x_xss_protection_disabled | 16 | 5/5 | 100% | ✅ | — |
| source_to_safe_template | 79 | 5/6 | 83% | ❌ (cross-file Py→template) | **3** |
| sql_regex_fallback | 89 | 5/5 | 100% | ✅ py2 fallback | — |
| xpath_taint_flow | 643 | 4/4 | 100% | 🟡 basic | **1** |
| get_state_change_branch | 352 | 4/4 | 100% | ❌ (GET that changes state) | **0** |
| redirect_taint | 601 | 3/3 | 100% | ✅ | — |
| plain_password_model_field | 256 | 3/3 | 100% | ✅ | — |

---

## Phase 0 — Quick high-precision wins ✅ DONE (held-out recall 48.3% → 50.9%)

Detectors at 73–100% precision, general, statically trivial. **Achieved +2.6pp held-out recall.**

- [x] `csrf_exempt` (CWE-352): `@csrf_exempt` disables CSRF on a view.
- [x] `sqlite_trace` (CWE-532): `conn.set_trace_callback(...)`.
- [x] `idor_strict_owner_absence` (CWE-639) — **the big one**: bare `current_user` presence no longer
      counts as ownership; ownership is enforced only if the user scopes the query / is compared to the
      object / access is denied. (was treating fetched-but-unused current_user as a check).
- [x] hardcoded credential as **kw-argument** (CWE-798): `User(password="password123")`,
      `connect(secret="...")` — any call with a credential-named kwarg = non-placeholder string literal.
- [ ] `get_state_change_branch` (CWE-352): a GET route whose body does a DB write (deferred — rare).
- [ ] `ccac_client_literal_gate` (CWE-16): client-level `verify=False` config gate (deferred).

**Result:** full corpus 51.6→53.6% recall / F2 50.9→52.2%; held-out 48.3→50.9% recall (crosses 50%),
precision held ~47%. At 53.6% mean recall ACR-QA now exceeds Opus 4.8 (51.7%) and Gemini 3.1 (52.6%)
on the leaderboard. **Validated the core thesis: combined-pipeline recall comes from the non-injection
detectors Semgrep can't do — NOT from duplicating its taint flow (Phase 1 deprioritised).**

---

## Phase 1 — Precise per-sink taint engine — ⚠️ DEPRIORITISED (Semgrep already covers it)

> **Finding (measured, 2026-06-22):** a generic inter-procedural taint pass was implemented and was
> **net-negative in the combined pipeline** — Semgrep already catches SQL/cmd/path/SSRF taint-flow,
> so our taint findings were duplicate-line FPs (precision 48.2%→46.3%). It only helps AST-only mode
> (kept opt-in via `ACRQA_INTERPROC_TAINT=1`). A *precise* per-sink engine (below) would still mostly
> duplicate Semgrep in the combined pipeline. **Lower priority than Phase 2 — build only if shipping
> a Semgrep-free pure-ACR-QA engine.** This is the honest re-prioritisation that drove the Phase-0 win.

This is kolega's moat. Replace the generic taint pass with **separate, sanitizer-aware, per-sink
taint detectors**. Value is in AST-only mode; combined-pipeline upside is marginal (Semgrep overlap).

Design (`CORE/engines/taint_analyzer.py` already exists — extend it / port concepts):
- [ ] **Per-sink taint** — `sql_taint_flow` (89), `path_taint_flow` (22), `ssrf_taint_flow` (918),
      `codeexec_taint` (94), `xpath_taint_flow` (643). Each: source → propagation → *specific* sink.
- [ ] **Param-specific wrapper summaries** — record *which parameter* of a helper reaches the sink
      (not "any arg"); only flag when *that* arg is tainted. (This is what made our generic attempt
      collapse — fix it here.)
- [ ] **Sanitizer awareness** — drop taint through `html.escape`, `shlex.quote`, `escape`,
      parameterized-query placeholders (`?`, `%s` with params tuple), `int()`/`os.path.basename` for
      paths. Use `config/taint_sanitizers.yml`.
- [ ] **Source breadth** — Flask/Django/FastAPI/Tornado/aiohttp/GraphQL-resolver params + `request.*`
      + env. Reuse `compute_function_taint`, made precise.

**Gate:** each sink detector must hold ≥75% precision on DEV before enabling. This is where the
combined-pipeline precision is won back (Semgrep overlaps, so dedup + only-fire-on-confident).

---

## Phase 2 — Auth / authz / IDOR recall detectors (recall-heavy, precision-risky)

kolega's #1 + IDOR. These trade precision for recall (it runs them at 43–53%). Gate carefully so we
don't tank combined precision. **Target: +4–6pp held-out recall; watch precision.**

- [ ] **authz-aware missing-auth** (CWE-306/862): route without auth AND (handles user-specific data
      OR admin path OR state-change) AND no module-level auth middleware. Refine current heuristic
      toward kolega's "strict, authz-aware, no-module-level".
- [ ] **auth_endpoint** (CWE-307): broaden login/auth-endpoint rate-limit detection (any
      authenticate/verify-password endpoint without a limiter decorator/middleware).
- [ ] **idor_strict_owner_absence** (CWE-639): object fetched by user-supplied id (`get(pk=request..)`,
      `objects.get(id=...)`) with NO ownership check (`current_user`, `owner ==`, `filter(user=...)`)
      in the same function. Strict owner-absence, not just query presence.

**Gate:** these add FPs by design — only ship if DEV+UNSEEN **F2** rises. Consider routing them to a
"medium-confidence" tier (Phase 4) rather than the default high-precision output.

---

## Phase 3 — Multi-file-type & cross-file (framework reach)

kolega scans JS and does cross-file Python→template taint. **Target: +2–4pp held-out recall.**

- [ ] **JS/DOM XSS** (`js_tainted_dom_sink`, `template_var_js_attr`, CWE-79): scan `.js` + inline
      `<script>` for `innerHTML`/`document.write`/`eval` with `location`/`document.URL`/template-injected
      vars. New file-type support.
- [ ] **source_to_safe_template** (CWE-79): cross-file taint — `render_template('t.html', x=tainted)`
      in Python → `{{ x | safe }}` / autoescape-off `{{ x }}` in the template. Join Python call args to
      template variables.
- [ ] **More template-var contexts**: variable rendered inside `<script>`, `href=`, `on*=` attribute
      (JS/URI context XSS even with HTML escaping).

---

## Phase 4 — Confidence tiering (the product differentiator)

kolega's `certain:` prefix = confidence tiers. ACR-QA already has the "Confirmed Tier" concept
(96.4% precision in the main product). Unify them for RealVuln. **Target: not recall — a
high-precision MODE + honest severity ranking.**

- [ ] Tag every finding with a confidence: `certain` (taint-confirmed / literal / 100%-prec
      detectors), `firm` (gated heuristics), `tentative` (auth/IDOR recall detectors).
- [ ] Two reporting modes: **recall mode** (all tiers, ~60% recall) and **confirmed mode**
      (`certain` only, ~85%+ precision). Report both numbers — beats kolega on *honesty* (it reports
      one blended number).
- [ ] Wire confidence into the SARIF/JSON output + dashboard severity.

---

# Beyond kolega — new & merged approaches (this is where we win)

Stealing kolega's detectors caps us at *its* design: a flat list of findings with one blended
precision number. The real leap is a **tiered, multi-engine trust architecture** that uses assets
no competitor has. Below, new phases ordered by (differentiation × feasibility).

## Phase 5 — Cross-detector agreement → a *deterministic* Confirmed Tier (HIGH value, low effort)

**Insight:** a finding flagged by **two independent detectors** (our AST + Semgrep, or two distinct
AST rules, or AST + Bandit) is dramatically more likely to be real. Agreement is a precision signal
we already generate and throw away. **No LLM, fully deterministic.**

- [ ] Tag each finding with the set of engines/rules that produced it (we already dedup by
      `(file, cwe, line)` — keep the provenance instead of collapsing it).
- [ ] **Confirmed Tier = agreement ≥ 2** independent sources. Measure its precision (expected ≫ 47%
      — likely 75–90%, matching kolega's `certain:` tier) and recall.
- [ ] Ship two official numbers: **recall mode** (union, ~54%) and **confirmed mode** (agreement,
      high precision). This is the honest version of kolega's `certain:` prefix — and it directly
      answers the "your precision is only 47%" critique with a real high-precision operating point.

> **✅ PROVEN (measured 2026-06-22):** AST∩Semgrep agreement = **78.6% precision** (44 TP / 12 FP) —
> matching kolega's `certain:` tier, fully deterministically. Agreement recall is low (7.9%) *because
> AST and Semgrep are complementary* (auth/config vs injection), which is exactly why their union
> recall is high. **Refinement:** Confirmed Tier = agreement(≥2) **OR** inherently-certain detectors
> (hardcoded-secret literal, debug=True, ReDoS catastrophic-pattern, eval/exec, weak-hash-of-credential
> — each ~100% precision by construction). This widens the high-precision tier without an LLM. The
> high-precision operating point a precision-focused buyer wants now demonstrably exists.

## Phase 6 — Ensemble expansion (MEDIUM value, low effort) — "steal from ALL tools, not just kolega"

We've been mining kolega. But Semgrep's *full registry* (not just our boost rules), CodeQL,
Bandit's high-precision subset, gosec, and even the LLM scan-results all catch TPs we miss. The
**union of all available detectors** is the true recall ceiling.

- [ ] Analyse FN vs **best-of-all-scanners** (not just kolega) — what does *nobody* catch (truly
      hard) vs what does *some* tool catch (recoverable)?
- [ ] Add Semgrep `p/python`, `p/django`, `p/flask`, `p/owasp-top-ten` registry packs (currently only
      custom boost rules). Dedup + route low-precision packs to the non-Confirmed tier.
- [ ] Re-add Bandit's **high-precision rules only** (B602/B608/B301/B324 — shell, SQLi, pickle, weak
      hash), excluded by a curated allowlist rather than running all of Bandit (which we dropped for FP).

## Phase 7 — Exploit-verification tier (HIGHEST differentiation) — merge ACR-QA's Docker detonation

**The moat no one else has.** ACR-QA already detonates findings live in a Docker sandbox
(`CORE/detection/`, exploit-verify engine, 5/5 verified per memory). kolega, Semgrep, and the LLMs
**flag**; ACR-QA can **prove**. Merge this into the RealVuln pipeline:

- [ ] For each high-severity finding in a runnable RealVuln repo, attempt automated detonation
      (spin the app, send the exploit input, observe the effect — SQLi data leak, RCE marker, path
      read of a sentinel file).
- [ ] **PROVEN tier = exploit-confirmed** → ~100% precision, *with a reproducible PoC*. No scanner on
      the leaderboard offers exploit-proven findings.
- [ ] Sign each proven finding with the existing ECDSA + Dilithium3 attestation → an auditable,
      tamper-evident "this vuln is real and here's the proof" artifact.
- [ ] Coverage will be partial (not every RealVuln repo is trivially runnable) — that's fine; PROVEN
      is a *premium tier on top of* recall mode, not a replacement.

## Phase 8 — Optional cheap-LLM precision filter (the ONLY path to top-F2; opt-in, non-deterministic)

The honest way to beat GPT-5.5 on **F2** specifically. Deterministic engine finds candidates (high
recall, $0); one **cheap single-shot LLM call** (Groq, already integrated) classifies each
non-Confirmed finding as exploitable / not. Promotes/demotes the tentative tier.

- [ ] Batch-classify tier-3 findings with a cheap model (~$0.50/repo vs the LLM agents' $35–62).
- [ ] Projected: ~54% recall × ~75% precision → **F2 ~60%**, beating every individual LLM agent on
      F2 *and* cost by 50×.
- [ ] **Strictly opt-in** (`--llm-filter`) so the default stays deterministic/$0. Report it as a
      *separate* mode — never conflate with the deterministic numbers. (Trades the determinism wedge
      for F2; offer both, let the user choose.)

## Phase 9 — Continuous external held-out corpus (validation infra; unblocks honest "beat kolega")

Our held-out is the 16 RealVuln repos we didn't tune on — but they're still *kolega's* corpus. The
unfakeable comparison needs repos **outside RealVuln entirely**.

- [ ] Clone 5–10 fresh intentionally-vulnerable Python repos NOT in RealVuln (e.g. OWASP PyGoat,
      django.nV, Vulnerable-Flask-App variants), hand-label or use their published CVE/finding lists.
- [ ] Freeze the engine; score on this truly-external set each release. **This number is the one a
      committee/HN cannot attack** — and lets us claim generalization vs kolega without its home field.
- [ ] Wire into CI as a slow nightly job.

---

# The unified vision — what "110% better than kolega" actually means

Not a benchmark row. A **tiered, multi-engine, provable trust system**:

```
                         ┌──────────── RECALL (union of all engines) ~55–60% ───────────┐
   AST engine  +  Semgrep registry  +  high-prec Bandit  +  (opt) LLM detectors
                         └──────────────────────────────────────────────────────────────┘
                                              │  every finding carries provenance
                                              ▼
   ┌─────────────────────── PRECISION TIERS (deterministic core) ───────────────────────┐
   │ PROVEN     exploit-detonated in Docker + ECDSA/Dilithium attested   → ~100% prec     │
   │ CONFIRMED  ≥2 independent detectors agree                            → ~80% prec      │
   │ FLAGGED    single detector                                           → ~50% prec      │
   │ (opt) LLM-filtered FLAGGED → promoted/demoted                        → ~75% prec, $   │
   └─────────────────────────────────────────────────────────────────────────────────────┘
```

**No competitor offers this combination:** kolega (closed, blended number, no proof), the LLM agents
($35–62, non-deterministic, no proof, no recall guarantee), Semgrep/Snyk (low recall). ACR-QA would
ship **frontier-range recall + a deterministic high-precision tier + exploit-proven findings +
attestation + $0 + reproducibility.** That is categorically better than a 95% benchmark number that
only holds on the author's own repos.

**Execution order:** see the ⭐ roadmap table at the top of this doc. In short — Confirmed Tier →
Exploit-proven tier → Ensemble recall → External held-out → JS/cross-file → opt-in LLM-filter (last).

---

## Measurement discipline (every phase)

1. **Held-out split is the oracle** — DEV = {dvpwa, djangoat, vfapi, vulnpy, tornado, pythonssti};
   UNSEEN = the other 16. Inspect/tune only on DEV; **judge only on UNSEEN.** Ship a detector only
   if UNSEEN F2 rises (or recall rises at held precision).
2. **Official scorer only** (`score.py`) — never the lenient inline number. See
   `realvuln_scorer_semantics`.
3. **No CWE-denylisting, no per-repo tuning** — taxonomy-fitting the held-out can't catch (advisor).
4. **Determinism is sacred** — `TESTS/test_static_scanner_determinism.py` must stay green; no
   set/dict ordering leaking into output.
5. **Re-run the leaderboard** (`realvuln_reliable_recall.py`) each phase to track position vs LLMs.

---

## Can we actually beat kolega? (the honest answer)

- **On RealVuln in-sample:** no — its 95% is 247 detectors tuned on these exact repos. Matching it
  means overfitting, which our held-out test rejects.
- **On held-out / generalization:** plausibly **yes** for *coverage* of the general detector set —
  and we can't measure kolega there (we only have its outputs on these 22 repos), so the honest
  comparison is our held-out number climbing toward frontier-LLM recall.
- **On the axes that matter for adoption:** **decisively yes.** kolega-enterprise is a closed
  commercial tool; ACR-QA is **free, deterministic, reproducible, auditable, $0**. If we reach
  ~60% held-out recall with confidence tiers, we are a *better product* than kolega for any team that
  needs a trustworthy, diffable CI gate — regardless of a few benchmark points.

**The real win condition:** ~60–65% held-out recall (beating frontier-LLM *typical* recall) +
a `certain`-tier high-precision mode + the determinism/cost/reproducibility wedge. That is "110%
better than kolega" where it counts — not a benchmark number we'd have to overfit to claim.
