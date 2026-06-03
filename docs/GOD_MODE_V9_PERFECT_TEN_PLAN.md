# ACR-QA God Mode Plan v9 — A *Real* 10 on Every Perspective

> **Created:** 2026-06-03
> **Author:** Ahmed Mahmoud Abbas
> **Trigger:** A fresh, code-grounded re-rating (not a doc re-read). The v8 plan claimed "18/18 at 10."
> A hard audit of the live tree says the honest average is **~7.0**. This plan closes the *measured*
> gap between 7 and a real 10 — where "real 10" means **the blocker is gone and provable on demand**,
> not "a box is checked in a doc."
>
> **Companion docs:** `GOD_MODE_V8_PERFECTION_PLAN.md` (the 20-perspective menu), `GOD_MODE_V7_
> COMPETE_PLAN.md` (tracks A–H), `ACTIVE_ROADMAP.md`. This plan supersedes v8's self-scoring.

---

## 0. The honesty correction (read first)

v8 says 18/18 at 10. The live tree says otherwise, and an examiner who senses inflation discounts
*everything*. The single most credible move in this entire plan is to **stop claiming a perfect score
we don't have** and instead show the work that earns each point. Audited facts, 2026-06-03:

| Claim in docs | Measured reality | Gap |
|---|---|---|
| "18/18 perspectives at 10" | Honest avg ≈ **7.0** | The inflation itself is a risk |
| OWASP "leads Youden J" | J = **0.157** (TPR 91% / **FPR 75.3%**) — near-random; only *relatively* ahead of Bandit 0.090 | The FPR is the #1 defense gotcha |
| "Verified Remediation — the frontier" | Real code, but **4 exploit categories** (sql/cmd/ssti/path), Docker-gated | Narrow; not yet 10+ |
| Confirmed Tier 96.4% precision | Real, but **n=55**, CI [90.9%, 100%] | Underpowered |
| "Engine platform" | **35 engine files**, 5 ADRs, bus-factor 1 | Reads as sprawl |
| Tests green | **2741 passed / 43 skipped**, mypy+ruff clean | ✅ genuinely solid |

**The v9 definition of a 10:** *I can hand the examiner one command (or one paragraph) that closes
the blocker on the spot.* Nothing counts until that's true.

---

## 0.5 Research-grounded corrections (deep-research pass, 2026-06-03)

External literature review changed three things in this plan. Citations are load-bearing — memorize them.

| What I had wrong / thin | The correction (with source) | Plan impact |
|---|---|---|
| "Plot the **ROC** curve" (#3) | For massively-imbalanced SAST data, **ROC masks the FPR** — the huge True-Negative count artificially depresses the x-axis. Use **Precision-Recall curve + PR-AUC** (the statistically-superior, examiner-recognized choice). SastBench plots exactly this Pareto frontier. | #2/#3 switch to **PR-AUC**, not ROC. |
| "Verified Remediation — the frontier nobody has" | **Commercially** unprecedented (Snyk/Copilot/Semgrep all re-*scan statically*), but **academically it's the 2025 vanguard** (both web-verified): **VulnRepairEval** (arXiv:2509.03331, Sept 2025) does the exact containerized differential — PoC compromises vuln container, *fails* on patched container; **CVE-Bench** (arXiv:2503.17332, ICML'25) evaluates by exploiting 40 real CVEs in containers. *(SymRadar/VulnFix were claimed by deep-research but could not be verified — do not cite.)* | Reposition honestly: *"surpasses commercial static re-scan; aligned with VulnRepairEval-class AVR."* Claiming pure novelty = an examiner who knows the paper sinks you. |
| SecurityEval dual-corpus as the FPR benchmark | SecurityEval/LLMSecEval/CyberSecEval are **generative-LLM** benchmarks — *no secure-code half*, so **useless for FPR**. Three real corpora **(I verified the GitHub repos exist, 2026-06-03)**: **RealVuln** (`kolega-ai/Real-Vuln-Benchmark` — 26 real Python repos, 676 vulns + 120 FP traps, recall-weighted F2, MIT), **BenchProctor** (`TheAuditorTool/BenchProctor` — SARIF-in/TPR-FPR-Youden-out, Apache-2.0), **xAST** (`alipay/ant-application-security-testing-benchmark` — Python soundness+completeness cases). | #4 becomes a **multi-benchmark** strategy (kills the "tested on your own data" trap). |

**Two more findings folded into the relevant rows below:**
- **Metrics:** Youden's J is what OWASP scores on, but security literature calls equal-weighting naïve (cost asymmetry — a miss >> a false alarm). Report **F2/F3** (recall-weighted) and **MCC** alongside. Reference point (real, web-verified): LLM-augmented SAST cuts false positives ~91% — Semgrep's AI layer + "Sifting the Noise" (arXiv:2601.22952) drive OWASP FP rates from 92% to ~6.3% — which is *exactly* what our Confirmed Tier does. That's the precedent that turns our FPR weakness into the textbook fix.
- **Calibration (#B5):** ECE + reliability diagrams are a recognized metric concept; per-rule **local Platt-scaling** is the cutting edge. *(The named comparables Gemini gave — DeepSecure/TaCCS-DFA — are fabricated; find a real ECE-for-SAST source before putting a number in the thesis.)* Our ECE<0.1 target is legit as a method.

---

## 1. The Perspective Scoreboard — current → 10, with the exact move

Each row: honest current score · the **one** blocker · the move that kills it · Definition of Done ·
effort. Sorted by leverage (FPR cluster first — it drags the most perspectives).

### Cluster I — The FPR / credibility story (fixes #2, #3, #18 — the biggest bleed)

| # | Perspective | Now | Blocker | Move → DoD | Effort |
|---|---|:--:|---|---|:--:|
| 2 | External examiner (skeptic) | 6.5 | 75.3% FPR reads as "screams on clean code" | **Report metrics per *tier*.** Compute TPR/FPR/precision/recall for **full output → Confirmed Tier** as *operating points on one PR curve* — Confirmed should land near-0 FPR / high precision. Precedent (real): Semgrep's AI layer + "Sifting the Noise" (arXiv:2601.22952) cut SAST FPs ~91% (92%→6.3% on OWASP) = our exact mechanism. → DoD: `OWASP_BENCHMARK.md` shows a 2-point PR table (full vs Confirmed) + one-line "which to merge against." | 1 day |
| 3 | CS researcher | 6.5 | J=0.157 alone looks weak; no curve | **Plot the PR curve + PR-AUC** across confidence thresholds (full → Confirmed). *PR, not ROC* — ROC masks FPR on imbalanced data. Add **F3** (recall-weighted) and **MCC** columns. A curve bowing above Bandit/Semgrep at every operating point is publishable, not embarrassing. → DoD: `pr_curve.png` + PR-AUC + F3 + MCC in the eval chapter. | 1–2 days |
| 18 | "Is it cooked?" | 7.5 | recall 91% / precision 96.4% sit confusingly close | **README restructure:** recall = headline (the win), precision = the *instrument* the gate uses. Frame as two operating points on one curve, never two bare numbers side by side. → DoD: README passes the "one-skeptic-question" read. | ½ day |

### Cluster II — Power the numbers (fixes #4, partially #3)

| # | Perspective | Now | Blocker | Move → DoD | Effort |
|---|---|:--:|---|---|:--:|
| 4 | Statistician | 6.5 | n=55 / n=89, wide CIs; SecurityEval has no secure-code half (can't measure FPR) | **Multi-benchmark, real FP traps (all 3 repos verified to exist):** Primary **RealVuln** (26 real repos, 676 vulns + 120 FP traps) → cross-validate **BenchProctor** (SARIF; quarterly-rotated, anti-leakage) → soundness/completeness **xAST** (`alipay`) → keep 20-CVE battery. → DoD: every headline stat CI < ±10pp; n>200; **MCC + F2/F3** columns; ≥2 independent corpora agree. | 2–3 days |

### Cluster III — Widen the moat (fixes #6, #10, strengthens #13)

| # | Perspective | Now | Blocker | Move → DoD | Effort |
|---|---|:--:|---|---|:--:|
| 6 | Security hiring mgr | 7.5 | 4 exploit categories | **Expand `exploit_verifier.py` 4 → 10+** using the safe observable signals in §1.5 below: SSRF (canary listener), XXE (canary-file UUID echo), insecure-deserialization (canary-file write via `__reduce__`), open-redirect (Location header), ReDoS (TTFB timing), LDAP-injection (mock OpenLDAP). Sandbox: `--network none`/isolated bridge, no egress. → DoD: ≥10 categories, each an exploit test red→green. | 4–5 days |
| 10 | Competitor | 8.0 | Verified Remediation narrow; novelty over-claimed | **Extend Verified Remediation to every new category** from #6 + **reposition honestly:** "commercially unprecedented; aligned with VulnRepairEval-class AVR (arXiv:2509.03331) + CVE-Bench (ICML'25); surpasses static re-scan." → DoD: ≥6 vuln classes with a fix *proven* to close the exploit in-sandbox; positioning cites the 2 verified papers. | rides on #6 |
| 13 | Auditor (SOC2/ISO) | 8.0 | evidence chain not demoed end-to-end | **One-command full chain:** `scan → exploit → autofix → re-exploit-fails → sign → Rekor → evidence pack`. → DoD: single script, public Rekor UUID resolves. | 1 day |

### Cluster IV — Kill the sprawl smell (fixes #7, #15, #17)

| # | Perspective | Now | Blocker | Move → DoD | Effort |
|---|---|:--:|---|---|:--:|
| 7 | Staff engineer | 6.5 | 35 engines = "what is all this?" | **`docs/architecture/ENGINE_MAP.md`:** one line per engine — purpose · status (core/experimental/eval-only/dead) · pipeline-critical? → DoD: every one of the 35 classified; the "why 35" question has a one-screen answer. | 1 day |
| 15 | Future-you | 6.5 | over-engineering regret | **Dead-code + coverage audit** (vulture + coverage on `CORE/`). Quarantine truly-dead engines; write a 1-page "what I'd cut" retro. → DoD: no 0%-coverage engine in the default pipeline without a documented reason. | 1 day |
| 17 | Maintainability | 6.0 | bus-factor 1, thin docs | **ADR backfill** (5 → ~12): one ADR per engine *cluster* explaining *why it exists*. CONTRIBUTING points a new dev to the right file in <5 min. → DoD: ADR per cluster; cold-start test on a fresh reader. | 1–2 days |

### Cluster V — Ops & UX proof (fixes #8, #11, #14, #12)

| # | Perspective | Now | Blocker | Move → DoD | Effort |
|---|---|:--:|---|---|:--:|
| 8 | SRE/DevOps | 7.5 | no live SLO proof | UptimeRobot + public status page; refresh k6/locust load test. → DoD: green status badge; `LOAD_TEST_RESULTS.md` current (p95/RPS). | ½ day + signup |
| 11 | Daily-user dev | 6.5 | latency, Docker friction | **`--fast` confirmed-only path** (skip full-output engines + Docker warmup) returning Confirmed Tier <30s; daemonless verify fallback. → DoD: measured <30s on `comprehensive-issues`. | 2 days |
| 14 | a11y user | 7.5 | no audited report | axe-core gate in Playwright; publish VPAT-lite. → DoD: axe gate green in CI; report in docs. | 1 day |
| 12 | Landing visitor | 7.5 | static, no "try it" | Hosted paste-code → Confirmed-findings demo (read-only, rate-limited). → DoD: public URL works on a phone. | 2 days |

### Cluster VI — Buyer trust (fixes #9)

| # | Perspective | Now | Blocker | Move → DoD | Effort |
|---|---|:--:|---|---|:--:|
| 9 | CISO / AppSec buyer | 5.5 | zero real users | **1 design partner** running it on a real repo (`DESIGN_PARTNER_OUTREACH.md`) + the signed evidence-pack demo. → DoD: one written "ran it on our repo, here's what it found" quote. | weeks (human) |

### Already near-10 — protect, don't touch

| # | Perspective | Now | Keep it there by… |
|---|---|:--:|---|
| 1 | Thesis examiner | 9.0 | filming the demo; dropping the "11/10" claim |
| 5 | Backend hiring mgr | 9.0 | the ENGINE_MAP so 35 files reads as *intentional* |
| 16 | Honesty police | 9.5 | publishing the unflattering OWASP J *and* the ROC that redeems it |

### The two that cannot be coded to 10 before defense (be honest, don't fake)

| # | Perspective | Now | Pre-defense ceiling | Real path to 10 | When |
|---|---|:--:|:--:|---|---|
| 19 | VC | 4.0 | **7** | revenue + retention + a team — calendar, not code | 6–18 mo post |
| 20 | OSS community | 4.5 | **7** | external contributors + stars + a cited spec — launch + time | 3–12 mo post |

> **The defense line that turns this into a 10-move:** *"Eighteen perspectives I drove to a real 10
> with code and rigor. Two — VC and community — need traction that takes months of adoption. A thesis
> is graded on the eighteen, and here's the honest runway for the two."* Saying the limit out loud
> beats faking it.

---

## 1.5 Safe-PoC signal spec — implementation-ready for the 6 new exploit categories (#6)

Sandbox rule for all: isolated Docker (`--network none` or egress-less bridge), no reverse shells, no
destructive payloads — only a **binary observable signal**. (No open-source Python safe-PoC framework
exists per the research, so this telemetry is itself a thesis contribution — say that.)

| Category | Safe payload | Observable signal (verified=exploit fired) |
|---|---|---|
| **SSRF** | inject `http://mock-listener:8080/ssrf-canary` (listener inside the isolated net) | mock listener logs a GET for the canary URI; patched → logs stay empty |
| **XXE** | `<!ENTITY xxe SYSTEM "file:///tmp/xxe_canary.txt">` (canary holds a random UUID) | HTTP response body reflects the UUID; patched → blank/error |
| **Insecure deser** (pickle/PyYAML) | `__reduce__` → `os.system('echo ACR-QA-Exploited > /tmp/pickle_canary')` | `docker exec` finds `/tmp/pickle_canary` with the string; patched → absent |
| **Open redirect** | redirect to `http://safe-sandbox-redirect.local`, client set to *not* follow | raw `Location` header == the sentinel host; patched → same-origin/blocked |
| **ReDoS** | evil string `(a+)+b` style; measure TTFB vs ~0.1s baseline | response time > 3.0s threshold = catastrophic backtracking; patched → baseline |
| **LDAP injection** | wildcard `*` / `)(uid=*))` into login vs an invalid password (mock OpenLDAP) | HTTP 200 + valid session on bad password = auth bypass; patched → 401 |

---

## 2. Sequencing — leverage-first, defense is the waypoint

| Phase | Window | Items | Why this order |
|---|---|---|---|
| **P0 — today** | hours | Commit the uncommitted hardening; **delete the "18/18 at 10" claim** from v8 + README | Free credibility; removes the inflation tax |
| **P1 — this week** | 3 days | #2, #3, #18 (the FPR/ROC story) + #4 (real OWASP corpus) | Kills the #1 gotcha and powers the numbers — the two things a skeptic attacks |
| **P2 — week 2** | 5 days | #6 (10+ exploits) → #10, #13 (one-command chain) | Widens the moat; makes the demo undeniable |
| **P3 — week 2–3** | 3 days | #7, #15, #17 (sprawl → ENGINE_MAP + dead-code + ADRs) | Three perspectives, mostly writing, high ROI |
| **P4 — week 3** | 3 days | #8, #11, #14, #12 (ops/UX proof) | Public artifacts + status + fast path |
| **P5 — pre-defense** | 2 days | Film demo; dry-run w/ Dr. Samy; memorize the FPR + reconciliation + runway answers | The human-gated 10-moves |
| **#9 + post** | weeks–months | design partner; VC/OSS runway | The traction 10s — start now, land later |

> **Hard rule:** if P2/P3 slip, ship **P0 + P1 + P5** and defend. That alone moves perspectives
> 2, 3, 4, 16, 18 to a real 10 — the five a skeptic actually probes.

---

## 3. What "perfect score" means for this plan

This plan succeeds when, **by defense day**, for each of the 18 code/rigor perspectives there exists
**one command or one paragraph** that closes its blocker live — and for the 2 traction perspectives,
the runway is *stated honestly* rather than faked.

| Floor (must) | Target | Stretch |
|---|---|---|
| Hardening committed; "11/10" claim removed; FPR/ROC story shipped (#2,#3,#18) | + real OWASP corpus, n>200 (#4) | + 10+ exploits & extended Verified Remediation (#6,#10) |
| ENGINE_MAP + dead-code audit (#7,#15) | + ADR backfill (#17) | + one-command audit chain (#13) |
| Demo filmed; answers memorized | + status page, `--fast`, a11y, live demo (#8,#11,#14,#12) | + 1 design partner quote (#9) |
| VC/OSS runway *stated* in defense | — | — |

**The one sentence:** *Close every measured blocker until each perspective has a one-command proof,
replace the perfect-score claim with the work that earns it, and make the act of distinguishing the
18 you can prove from the 2 you can't the most credible thing said in the room.*

---

## 4. Anti-scope-creep guardrails

1. **No item ships without its DoD met + tests green.** No half-tracks.
2. **The FPR/ROC story (P1) is non-negotiable and comes first** — it's the highest-leverage half-day in the project.
3. **Honesty over headline.** Publish the unflattering number next to the curve that explains it.
4. **More engines is now negative.** Adding code lowers #7/#15/#17. Build *only* what's on this list.
5. **Don't fake the traction 10s.** No vanity stars, no "users" who are you.

---

## 4.5 Defense armor — the honesty framing that turns weaknesses into rigor

These serve perspectives #1, #2, #16 directly and cost nothing to write. Memorize the framings, not just the facts.

### The 3 classic traps that sink security-tool defenses (preempt all 3 in the thesis text)

| Trap | The objection | Our preemption |
|---|---|---|
| **Synthetic benchmark** | "95% on Juliet/OWASP is a dataset artifact, not real-world skill." | We evaluate on **RealVuln + BenchProctor + xAST** (real, multi-file, with FP traps). We *openly state* real-world scores are lower (50–70% F-range) and frame that as **methodological honesty**, not weakness. |
| **Data contamination** | "You tuned rules on the same repos you tested on / the LLM saw these CVEs in training." | Cryptographic train/eval separation (commit-SHA-pinned corpora); the 20-CVE holdout battery; document it. |
| **Engineering vs. novelty** | "You piped Semgrep JSON into an LLM + subprocess. Where's the CS?" | The contribution is **not the plumbing** — it's the *translation layer*: static finding (source, sink, line, inferred types) → a deterministic dynamic exploit constraint, re-run before+after the fix. That bridge is the novelty. |

### The soundness/completeness statement (say this, it reads as mastery)

By **Rice's theorem** no static analyzer is both sound and complete for a Turing-complete language; Python's
duck typing, monkey-patching, `getattr`/`eval`, decorators and late binding make a *sound* inter-procedural
CFG computationally intractable. So state it plainly:

> *"The SAST layer makes no claim to formal soundness. It is a high-recall heuristic filter for common
> web-framework topologies; its well-documented false-positive cost is **the exact motivation** for the
> dynamic exploit-verification phase, which delegates the proof of exploitability to a deterministic
> runtime. The hybrid trades static **completeness** (can't prove absence of all bugs) for **precision**
> (every *verified* finding is a genuine, exploited threat) — and re-runs the exploit after the fix for
> runtime proof of remediation that static delta-analysis cannot give."*

Precedent for phrasing limits as scope, not apology: **Meta's Pysa docs** ("there is no way to build a
perfect static analyzer… Python, as a dynamic language…"). Cite it.

### Reachability = the *floor* of exploitability (frames the B3 reachability score honestly)

3 tiers: dependency-level (SCA) → function-level (call graph) → contextual/data-flow (taint). Even perfect
taint proves *reachable*, not *exploitable* — runtime sanitizers, framework auto-escaping, WAFs sit above it.
**Reachability proves a vuln *might* fire; our exploit-verification proves it *does*.** EPSS/KEV only cover
*known public CVEs in dependencies* — they cannot speak to first-party code, which is exactly why first-party
exploitability must be *proven computationally*, finding by finding. That's the gap the tool fills.

---

## 5. Citations to memorize (the defense-armor)

> **Verification status (checked 2026-06-03):** ✅ = I confirmed the GitHub repo exists. ⚠️ = claimed by
> deep-research but **not yet verified** (future-dated arXiv IDs — read the paper before citing as fact).

| ✓ | Topic | Source | Use it to… |
|:--:|---|---|---|
| ✅ | Real Python corpus w/ FP traps | **RealVuln** — github.com/kolega-ai/Real-Vuln-Benchmark (MIT, F2) | justify FPR measurement on *real* code |
| ✅ | Cross-validation corpus | **BenchProctor** — github.com/TheAuditorTool/BenchProctor (Apache-2.0, SARIF) | second independent corpus; anti-leakage |
| ✅ | Soundness/completeness | **xAST** — github.com/alipay/ant-application-security-testing-benchmark | algorithmic soundness/completeness on Python |
| ✅ | Brand-name benchmark | **OWASP BenchmarkPython** — github.com/OWASP-Benchmark/BenchmarkPython | the recognizable name (beta) |
| ✅ | Limits-as-scope precedent | **Meta Pysa docs** ("no perfect static analyzer… Python dynamic…") | phrase soundness limits as rigor |
| ✅ | Why PR not ROC | Google ML crash course (ROC masks FPR on imbalance) | defend the PR-AUC choice |
| ✅ | Exploit-based fix eval (AVR) | **VulnRepairEval** — arXiv:**2509.03331** (Sept 2025); containerized differential, top LLM 5/23=21.7% | the cornerstone: position Verified Remediation as same-paradigm-as-vanguard, ahead of commercial static re-scan |
| ✅ | Exploitability benchmark | **CVE-Bench** — arXiv:**2503.17332**, ICML'25 spotlight, github.com/uiuc-kang-lab/cve-bench; 40 CVEs in containers w/ reference exploits | the precedent for "evaluate by exploiting, not detecting" |
| ✅ | Multi-commit Python benchmark | **CrossCommitVuln-Bench** — github.com/motornomad/crosscommitvuln-bench; 15 CVEs, 87% invisible to per-commit SAST | optional 4th corpus; the "snapshot SAST misses chains" angle |
| ✅ | FP-cut precedent (real) | **Semgrep AI** blogs + **"Sifting the Noise"** arXiv:2601.22952 + InfoWorld — LLM verification cuts SAST FPs ~91% (92%→6.3% on OWASP) | frame Confirmed Tier as the textbook move |
| ✅ | Reachability prior art | **SAVANT** — arXiv:2506.17798 (Jun 2025); semantic-guided reachability **(Java, not Python — note it)** | position reachability scoring honestly |
| ⚠️ | Cost-asymmetric metric | RealVuln **F2/F3** (recall-weighted); **MCC** for imbalance | answer "why not just F1?" |
| ⚠️ | Confidence calibration | per-rule Platt-scaling; ECE-for-vuln-detection concept is real *(find a real named source before citing)* | justify ECE<0.1 |
| ❌ | **DO NOT CITE — fabricated** | **SymRadar**, **DeepSecure (ECE 0.19)**, **QASecClaw**, **TaCCS-DFA** — absent from Gemini's own source list AND unfindable on the web (2026-06-03). Gemini prose hallucinations. | — |

**The one honest sentence about novelty:** *"Re-running the exploit to verify the fix is unprecedented
among commercial SAST/SCA vendors, who re-scan statically; it aligns with the 2025 academic vanguard of
exploit-based evaluation (VulnRepairEval, arXiv:2509.03331; CVE-Bench, ICML'25) and brings that rigor
into an integrated, attested, production-shaped tool."* — both citations web-verified 2026-06-03.

---

*Plan v9 created 2026-06-03. Supersedes v8's self-scoring with a code-grounded re-rating; executes the
open tracks of v7/v8 against the gaps that an actual audit — not a doc read — surfaced. §0.5 + §1.5 + §5
incorporate a deep-research literature pass (2026-06-03).*
