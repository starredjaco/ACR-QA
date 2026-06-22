# Plan: Match & Beat kolega-enterprise — Phased Detector Roadmap

> **Goal:** make ACR-QA's deterministic engine match or beat kolega-enterprise's detection
> *coverage* on a **held-out** basis, then win decisively on the axes kolega can't touch
> (free, deterministic, reproducible, auditable). Status as of 2026-06-22.

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
