# ACR-QA God Mode v10 — The Real 10 Roadmap (Research-Grounded)

> **Created:** 2026-06-04 · **Author:** Ahmed Mahmoud Abbas
> **Trigger:** A harsh, code-grounded product re-rating + a web-VERIFIED deep-research pass.
> **Supersedes:** the scoring in `GOD_MODE_V9_PERFECT_TEN_PLAN.md`. Executes its open tracks against
> verified 2026 market reality.
>
> **Definition of a real 10:** *one command or one paragraph closes the blocker live* — not a box ticked
> in a doc. Two perspectives (traction, raw-recall) have honest ceilings; we state them, we don't fake them.

---

## 0. The two honest ceilings (read first)

| Perspective | Why it can't be a naive 10 by defense | The honest 10-move |
|---|---|---|
| **Traction / adoption** | Real users/stars/partners take months. Code can't buy it. | **State the go-to-market runway out loud** and score it honestly. Faking stars = instant credibility death. |
| **Raw absolute recall** | You will not out-detect Snyk/Semgrep solo. | **Reframe to scope-bounded recall on real corpora.** RealVuln (verified) proves traditional SAST gets ~17% on real Python — so 25%/48% is a *win*, not a weakness. |

Everything else can hit a genuine 10.

---

## 1. Verified research (web-checked 2026-06-04, load-bearing — see `memory/research_2026_06_verified.md`)

| Claim | Status | Consequence |
|---|---|---|
| **RealVuln** arXiv:2604.13764 — Semgrep 17.5%, Snyk F3 17.4, SonarQube 6.5%, Claude Sonnet 4.6 ~50%, Kolega.Dev 80.9% | ✅ REAL | Recall reframes from weakness → headline. ACR-QA 25%/48% beats all rule-based tools. |
| **RuleForge** arXiv:2604.01977 (JHU+AWS) — LLM-as-judge **ECE 0.17**, AUROC 0.75 | ✅ REAL | The real, citable ECE source. Replaces fabricated DeepSecure/TaCCS-DFA. |
| **Qualys TruConfirm / Agent Val** (Feb–Mar 2026) — re-detonates exploit after patch | ✅ REAL | **Kills "commercially unprecedented."** Reposition required. |
| **ZeroPath** — AI-native SAST+DAST, exploit proof + fix verification | ✅ REAL | Closest direct competitor. |
| "Ghost Security CAST report, 99.5% FP, arXiv:2604.13764" | ❌ FABRICATED | Gemini reused RealVuln's ID. Do NOT cite the 99.5% number. |

**The repositioning sentence (replaces every "unprecedented" claim):**
> *Exploit-verified remediation became the 2026 vanguard — Qualys & ZeroPath commercialized it;
> VulnRepairEval & PatchEval institutionalized it academically. ACR-QA independently converges on the same
> paradigm for **first-party application source code, in CI, ECDSA-attested, at $0** — and names the true
> frontier (autonomous PoC generation + self-healing feedback, EvoRepair/SEC-bench) as future work.*

---

## 2. The Perspective Scoreboard (current → 10)

| # | Perspective | Now | Blocker | Move → DoD |
|---|---|:--:|---|---|
| 1 | **Installability** | 2 | `pip install acrqa` → "No matching distribution" | PyPI publish. → `pip install acrqa && acrqa --help` from clean venv. |
| 2 | **Detection / recall** | 4 | Looks low in a vacuum | Run RealVuln harness; report on its leaderboard. → ACR-QA shown beating Semgrep/Snyk/SonarQube + 3-number framing (91% SecurityEval / 48% RealVuln-detectable / 25% full). |
| 3 | **Trust wedge (exploit-verify)** | 7 | Only 3/10 categories really detonated; "unprecedented" false | Detonate the other 7 (red→green) + drop "unprecedented" + convergence paragraph. → `EXPLOIT_VERIFICATION.md` shows 10/10 real. |
| 4 | **FPR / calibration credibility** | 3 | 75.3% FPR raw; no calibration number | Confirmed Tier = default output; PR-curve + PR-AUC + F2/F3 + MCC; compute ECE, cite RuleForge 0.17. → clean repo = 0 default false alarms; ECE in eval chapter. |
| 5 | **Engineering quality** | 7.5 | 137 broad `except Exception`; silent failure | Audit each → narrow or log+re-raise in trust-critical paths. → no silent swallow on the verify path. |
| 6 | **Focus / product surface** | 4 | 37 engines reads as sprawl | Engine facade + ENGINE_MAP; README leads with ONE sentence. → one-headline README. |
| 7 | **Differentiation / moat** | 7 | Moat closed; novelty over-claimed | Honest convergence paragraph + competitor table (re-exploit-to-verify vs static re-scan). → defensible 1-paragraph novelty line, verified cites only. |
| 8 | **Traction / adoption** | 1 | No users (structural) | State GTM runway honestly. → defense slide: "18 provable, 2 need traction." |
| 9 | **Frontend / UX** | 5 | No local `dist` build | Build dist + a11y pass + deploy proof. → live URL or built dist. |
| 10 | **Docs / honesty** | 8 | Already strong | 3-number framing everywhere; reconciliation as a paper section. → every headline stat has corpus + CI. |

---

## 3. Phased execution (DoD-gated, owner-tagged)

### P0 — Make it exist (unblocks everything) · 1–2 days
| # | Item | Owner | DoD |
|---|---|---|---|
| 1.1 | Build wheel + sdist; fix `pyproject` packaging/entry-points | **Claude** | `python -m build` clean; local wheel install runs `acrqa --help` |
| 1.2 | PyPI Trusted Publisher (OIDC) setup | **Ahmed** | "acrqa" project created, OIDC publisher added |
| 1.3 | Tag → publish workflow | **Claude** | `pip install acrqa` from clean venv works → **#1: 2→9** |

### P1 — Make the wedge undeniable + fix the FPR story · 4–6 days
| # | Item | Owner | DoD |
|---|---|---|---|
| 3.1 | Real detonation for the 7 untested categories (ssrf/xxe/deser/redos/ldap/open-redirect/path), red→green | **Claude** (Docker) | `EXPLOIT_VERIFICATION.md` = 10/10 real → **#3: 7→9** |
| 3.2 | Extend Verified Remediation to each new category | **Claude** | ≥8 classes: fix proven to kill exploit in-sandbox |
| 4.1 | Confirmed Tier = **default** output; noisy tier opt-in `--all` | **Claude** | clean repo → 0 default false alarms → **#4: 3→7** |
| 4.2 | PR-curve + PR-AUC + F2/F3 + MCC; compute ECE, cite RuleForge 0.17 | **Claude** | `pr_curve.png` + ECE in eval chapter → **#4: 7→9** |

### P2 — Detection within a defensible scope · 2–3 days
| # | Item | Owner | DoD |
|---|---|---|---|
| 2.1 | Run ACR-QA through RealVuln's own harness; report on its leaderboard | **Claude** | ACR-QA placed vs Semgrep/Snyk/SonarQube, CIs, 3-number framing → **#2: 4→8** |
| 2.2 | LLM-augment default-on-with-gate (the +5.2pp held-out win) | **Claude** | union-gated recall live in `main.py`, precision held |

### P3 — Kill the sprawl & harden · 3–4 days
| # | Item | Owner | DoD |
|---|---|---|---|
| 5.1 | Audit 137 `except Exception` → narrow / log+re-raise | **Claude** | no silent swallow in trust path → **#5: 7.5→9.5** |
| 6.1 | Engine facade + ENGINE_MAP; one-headline README | **Claude** | README leads with ONE sentence → **#6: 4→8** |
| 9.1 | Frontend `dist` build + a11y pass + deploy proof | **Claude** + **Ahmed** (deploy) | live URL or built dist → **#9: 5→9** |

### P4 — Honesty & positioning · 1–2 days
| # | Item | Owner | DoD |
|---|---|---|---|
| 7.1 | Drop "unprecedented" everywhere; convergence paragraph + competitor table | **Claude** | verified cites only → **#7: 7→9** |
| 10.1 | 3-number framing everywhere; reconciliation as paper section | **Claude** | every headline stat has corpus + CI → **#10: 8→9.5** |
| 8.1 | GTM runway stated + scored honestly in defense deck | **Ahmed + Claude** | "18 provable, 2 need traction" slide → **#8: honest 7** |

---

## 4. Anti-scope-creep guardrails

1. No item ships without DoD met + tests green.
2. **PyPI (P0) is non-negotiable and first** — an uninstallable tool can't claim convergence with anything.
3. **More engines is now negative** (lowers #6). Build only what's on this list.
4. **Honesty over headline.** Drop "unprecedented"; publish the unflattering number next to the curve that explains it.
5. **Don't fake the traction 10s.** No vanity stars, no "users" who are you.
6. **Verify every Gemini number against the web before it touches the thesis** (one fabrication already caught).

---

## 5. Citations to memorize (all web-verified 2026-06-04)

| Topic | Source | Use it to… |
|---|---|---|
| Real Python recall baseline | **RealVuln** arXiv:2604.13764 / realvuln.kolega.dev | prove traditional SAST = ~17%; position 25%/48% as a win |
| ECE for LLM-judged vuln confidence | **RuleForge** arXiv:2604.01977 (JHU+AWS) — ECE 0.17 | the real calibration bar (replaces fabricated cites) |
| Exploit-based fix eval (academic) | **VulnRepairEval** arXiv:2509.03331 · **PatchEval** arXiv:2511.11019 · **SEC-bench** arXiv:2506.11791 | position Verified Remediation as same-paradigm-as-vanguard |
| Exploitability benchmark | **CVE-Bench** arXiv:2503.17332 (ICML'25) | "evaluate by exploiting, not detecting" precedent |
| Commercial moat (now closed) | **Qualys TruConfirm/Agent Val** (Feb–Mar 2026) · **ZeroPath** | the honest reason to drop "unprecedented" |
| True frontier (future work) | **EvoRepair** arXiv:2605.30105 · **SEC-bench** | name the next frontier: autonomous PoC gen + self-healing |
| **DO NOT CITE — fabricated** | "Ghost Security CAST, 99.5% FP" · DeepSecure · TaCCS-DFA · QASecClaw · SymRadar | — |

---

## 6. Strategic Architectural & Product Enhancements (Post-Review Feedback)

To push the system from a 9.4 to a perfect 10.0 overall, the following high-impact initiatives have been identified:

| Initiative | Description | Impact |
|---|---|---|
| **MicroVM Sandboxing** | Evolve the Proof-of-Exploit engine from standard Docker containers to AWS Firecracker microVMs or gVisor. | True multi-tenant, sub-second isolation for safer DAST execution. |
| **Deterministic AI Output Testing** | Implement rigorous automated evaluations (e.g., RAGAS or LangSmith) for the Explanation Engine. | Continuously measures and mitigates hallucination rates as underlying LLMs update. |
| **Monetization / SaaS Readiness** | Hook up Stripe to the FastAPI backend and launch a self-serve cloud tier based on existing billing docs. | Transitions the project from a brilliant thesis into a lucrative, scalable business. |

These items are to be considered for **P5** or long-term post-defense roadmap execution.

---

*Plan v10 created 2026-06-04. Grounded in a harsh product re-rating + a web-verified deep-research pass.
The single most credible move remains: stop claiming a perfect score we don't have, and show the work
that earns each point — now against the live 2026 market, not a 2025 snapshot.*
