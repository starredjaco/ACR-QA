# ACR-QA Active Roadmap — Ahmed's Personal Execution Plan

> ## ⭐ CURRENT STATE (2026-06-24) — defense done, RealVuln #1
>
> **The engine is now #1 on recall among all external scanners on RealVuln 2026.** These supersede
> every earlier RealVuln number in the historical task log below (25.1% / 37.8% / 50% / 53% etc.):
>
> - **RealVuln full corpus (official): 58.8% recall / 46.3% precision / F2 55.8%** — edges out
>   GPT-5.5 (58.2%), beats Opus 4.8 (51.7%), Gemini 3.1 (52.6%), Semgrep 17.6%, Snyk 14.9%, at **$0**.
> - **Held-out (16 never-seen repos): 53.0%** · **external (PyGoat): 48.1%** · deterministic, 100% reproducible.
> - **Deterministic Confirmed tier: 80.6% precision** (≥2-engine agreement, no LLM).
> - **3,147 tests · 88% CORE coverage** · ECDSA-P256 **+ real post-quantum Dilithium3** attestation.
> - Method + full results: [`evaluation/REALVULN_PURE_STATIC_2026_06_22.md`](evaluation/REALVULN_PURE_STATIC_2026_06_22.md),
>   [`evaluation/KOLEGA_PARITY_PLAN.md`](evaluation/KOLEGA_PARITY_PLAN.md). Defense: DONE. Now: open-source launch + job search.

> **What this is:** The actual execution log for ACR-QA v5.0.0. All items below are
> **completely free** (no domain, no card, no surprise bills) and realistic for a
> fresh-grad backend + DevOps engineer.
>
> **Current plan:** [`GOD_MODE_V11_PERFECT_TEN_ALL_PERSPECTIVES.md`](GOD_MODE_V11_PERFECT_TEN_ALL_PERSPECTIVES.md) —
> dual-scoreboard (thesis + startup) repositioning. Supersedes v10; grounds every claim in
> web-verified 2026 literature.
>
> **Archive (do not re-execute):** v4–v10 God Mode plans — superseded, moved to
> [`archive/`](archive/). Strategic menu for post-defense: [`GOD_MODE_V5_PLAN.md`](archive/GOD_MODE_V5_PLAN.md).
>
> **Created:** 2026-05-31 · **v10 repositioning:** 2026-06-04 · **Last updated:** 2026-06-21
> **Defense DELIVERED:** 2026-06-19 ✅ · **Now:** open-source launch + job search
> **Total cost:** $0 ongoing. $0 setup.

---

## The 15 Items I'm Actually Doing

| # | Item | Time | Status | Why this one |
|---|------|------|--------|--------------|
| 1 | **Funnel reveal slide** (1,942 → 55 → 96.4% precision) | 1 hour | ✅ | `docs/FUNNEL_SLIDE.html` — interactive Space/→ presenter slide |
| 2 | **Docker image on `ghcr.io/ahmed-145/acrqa`** | 2 days | ✅ | `.github/workflows/sign-images.yml` — builds, pushes, Cosign-signs |
| 3 | **75-sec LinkedIn marketing video** | 1 day | 📋 | **Ahmed records** — SecureHub-style script at `docs/business/VIDEO_SCRIPT.md` |
| 4 | **README + Codespaces "Open in" button** | 1 day | ✅ | `.devcontainer/devcontainer.json` + Codespaces badge in README |
| 5 | **Cloudflare Pages static dashboard** at `acrqa.pages.dev` | 2 days | ✅ | `cloudflare-pages/index.html` ready — **Ahmed deploys via CF dashboard** |
| 6 | **5-rater κ study** (closes the "in progress" eval gap) | 2.5 weeks | ✅ | `docs/kappa_study/` — materials + analyze_kappa.py — **Ahmed recruits raters** |
| 7 | **GitHub webhook receiver** (PR → autoscan → comment) | 1–2 weeks | ✅ | `.github/workflows/acr-qa.yml` — already fully working |
| 8 | **VS Code extension** (free Marketplace listing) | 1–2 weeks | ✅ | `vscode-extension/` — TypeScript + server/standalone modes — **Ahmed publishes** |
| 9 | **Multi-LLM jury** (Groq + Gemini free tiers only) | 3 days | ✅ | Gemini 1.5-flash added to `second_opinion.py`; falls back gracefully |
| 10 | **Cosign + SLSA L3 + Sigstore Rekor** | 2 days | ✅ | `sign-images.yml` upgraded with `slsa-github-generator` L3 job |
| 11 | **Self-scan badge** on README | 1 hour | ✅ | `.github/workflows/self-scan.yml` — weekly, commits badge JSON |
| 12 | **Hacker News post + LinkedIn article + blog** | 1 day | 📋 | `docs/business/LAUNCH_POSTS.md` — copy-paste ready — **Ahmed posts (defense done ✅)** |
| 13 | **Differential SAST** — new-only findings vs. last scan | 3–5 days | ✅ | `GET /v1/runs/{id}/diff` + `Database.get_run_by_id` |
| 14 | **Counterfactual explanations** — "what would fix this?" | 3–5 days | ✅ | `POST /v1/findings/{id}/counterfactual` + `ExplanationEngine.generate_counterfactual()` |
| 15 | **Kubernetes operator with CRDs** — `ACRQAScan` CRD | 2–3 weeks | ✅ | `deploy/operator/` — kopf controller + RBAC + example CR |

**Total work:** ~8–9 weeks of focused effort
**Total ongoing cost:** $0
**Total setup cost:** $0 (no card required for any of the above)

---

## v6 Phase 0 — Trust-Layer Repositioning (2026-06-02)

These items execute the one-sentence bet from `GOD_MODE_V6_BUSINESS_PLAN.md`. All $0.

| # | Item | Status | What changed |
|---|------|--------|--------------|
| 16 | **README rewrite** — lead with trust/verify/attest, not "19 engines" | ✅ | New hero section, competitive table, funnel as first visual |
| 17 | **Cloudflare Pages rewrite** — same repositioning | ✅ | Full landing page rebuild: trust pillars, exploit table, competitor grid |
| 18 | **`CORE/engines/confirmed_tier.py`** — Confirmed Tier as a proper CORE module | ✅ | Extracted + enhanced with reachability gate; wired into both pipeline paths |
| 19 | **Verification data loop** — `verification_log` table + `db.log_verification()` | ✅ | Schema + Database methods + exploit_verifier auto-logging (Moat #1) |
| 20 | **Dashboard overview** — Confirmed Tier as hero tile + Trust Layer banner | ✅ | Green banner with 4 trust KPIs; Confirmed Tier is the first bento tile |
| 21 | **Design-partner outreach template** | ✅ | `docs/DESIGN_PARTNER_OUTREACH.md` — email + LinkedIn templates + target repo list |

**Phase 0 exit metric:** a stranger watches the demo and says *"I'd turn that on as a required check."*

---

## v6 Phase 1+2+3 — Proof, Monetize, Moat (2026-06-02)

| # | Item | Phase | Status | What it does |
|---|------|-------|--------|--------------|
| 22 | **Verification stats API** (`GET /v1/verification/stats`, `GET /v1/verification/log`) | 1 | ✅ | Exposes the data-loop health — labeled ground truth accumulating from real scans |
| 23 | **Confirmed Tier API filter** (`?confirmed=true` on `/v1/runs/{id}/findings`) | 1 | ✅ | Buyers can filter to only the 96.4%-precise findings in any API call |
| 24 | **`GET /v1/runs/{id}/confirmed-summary`** | 1 | ✅ | Per-run confirmed count, signal breakdown, auto-block-safe flag |
| 25 | **BYO-LLM-key** (`--llm-key` CLI + `LLM_API_KEY` env var) | 2 | ✅ | Enterprise customers use their own Groq key — kills data-objection and cost-objection |
| 26 | **`GET /v1/runs/kpi/confirmed-fix-rate`** | 2 | ✅ | The company metric: % of Confirmed findings marked fixed (target >70%) |
| 27 | **AI-code differential mode** (`--ai-code-diff` CLI flag) | 1 | ✅ | `AiCodeDiffFilter`: git-log + file-header heuristics detect Copilot/Cursor/Claude-touched files; only surfaces findings in those files |
| 28 | **SARIF confirmed_tier field** + `--confirmed-only` export flag | 2 | ✅ | GHAS upload contains `acrqa/confirmed_tier` property; `--confirmed-only` uploads only the 96.4%-precise stratum |
| 29 | **GitHub Action — Confirmed Tier merge gate** | 2 | ✅ | New required check: counts confirmed findings, fails merge if >0, posts exact count as annotation |
| 30 | **Compliance evidence pack** (`scripts/generate_evidence_pack.py`) | 3 | ✅ | HTML+JSON evidence bundle for SOC2/ISO27001/EU CRA auditors; includes attestation signatures + Rekor log indexes |
| 31 | **P-1 benchmark script** (`scripts/run_benchmark_p1.py`) | 1 | ✅ | Runs ACR-QA vs Bandit vs Semgrep on SecurityEval dataset; Wilson CI; pre-registered methodology |
| 32 | **P-1 methodology pre-registration** (`docs/evaluation/P1_BENCHMARK_METHODOLOGY.md`) | 1 | ✅ | Methodology committed before any run — makes results falsifiable, not marketing |
| 33 | **P-2 leaderboard page** (`cloudflare-pages/benchmark.html`) | 2 | ✅ | Public benchmark page with live results, methodology links, reproduce-in-2-commands |
| 34 | **Verified Finding open spec** (`schemas/verified_finding_v1.schema.json`) | 3 | ✅ | JSON Schema for the open standard — claim + exploit evidence + signature. Moat #4. |

**Phase 1 exit metric:** public benchmark page + ≥3 case studies (design partners — Ahmed recruits).
**Phase 2 exit metric:** first revenue + fix rate >70% (instrument KPI endpoint).
**Phase 3 exit metric:** one enterprise contract + one external party cites the Verified Finding spec.

---

## v7 Detection Gap-Closing (2026-06-03)

| # | Item | Status | Result |
|---|------|--------|--------|
| 35 | **7 taint rules (pass 1)** — open redirect, log injection, LDAP injection, ReDoS, XSS, JWT bypass | ✅ | Recall 58.4% → **78.7%** |
| 36 | **16 gap-closing rules (pass 2)** — HTTP response splitting, traceback exposure, empty DB password, hardcoded salt, FTP cleartext, NoSQL injection (DynamoDB), OpenSSL no-verify, ssl.wrap_socket, SHA-256 password hash, hardcoded API key, infinite loop, os.system fstring, path traversal via os.remove, dynamic exec, CWE-319/321/327/521/760/835/943 | ✅ | Recall 78.7% → **91.0%** [82.8%, 97.8%] |
| — | **Rule count:** 42 → 56 → **86** total custom Semgrep rules | ✅ | |
| — | **RECONCILIATION.md** — honest P-1 retraction + P-2 methodology | ✅ | |

---

## v8 Tracks (2026-06-03)

| # | Item | Status | Result |
|---|------|--------|--------|
| 37 | **Version sync** — 5 disagreeing strings → all `5.0.0rc1`; regression test added | ✅ | `--version` prints correctly; `TestVersionConsistency::test_all_version_sources_agree` |
| 38 | **OWASP-Methodology Benchmark** — dual corpus (89 TP + 89 TN); Youden J, FPR, MCC, CIs | ✅ | J=0.157 leads Bandit 0.090 + Semgrep 0.056; §5.18 in EVALUATION_CHAPTER; Q41-Q42 in QA_PREP |
| 39 | **Verified Remediation Engine** — 5-step detect→exploit→patch→re-exploit→sign pipeline | ✅ | `CORE/engines/verified_remediation.py`; 15 unit tests; demo script; §5.19 in EVALUATION_CHAPTER; Q43 in QA_PREP |
| — | **Benchmark.html + cloudflare pages** — OWASP leaderboard + Verified Remediation section added | ✅ | Public-facing pages now reflect full benchmark story |
| — | **All test badges** synced to 2,759 | ✅ | README + cloudflare + QA_PREP |

**Current best numbers (SecurityEval, genuinely-vulnerable, bootstrap 95% CI):**
- ACR-QA full output recall: **91.0%** [82.8%, 97.8%] vs Bandit 50.6% vs Semgrep 23.6%
- OWASP Youden J (dual corpus): **0.157** vs Bandit 0.090 vs Semgrep 0.056
- Confirmed Tier precision: **96.4%** [90.9%, 100%] on 30-repo production corpus
- Verified Remediation: **`fix_verified=True`** provable — live exploit re-run after fix

---

## v9 Tracks (2026-06-03) — code-grounded re-rating, closes all measured gaps

| # | Item | Status | Result |
|---|------|--------|--------|
| P0 | **Remove "11/10" / "18/18 at 10" inflation claims** from v8 plan + ACTIVE_ROADMAP | ✅ | Honest avg ~7.0 acknowledged; v9 commits the v8 plan fix |
| P1.1 | **PR Curve + F3 + MCC operating-point analysis** (PR not ROC for imbalanced data) | ✅ | `scripts/run_pr_curve_analysis.py`; 5 operating points; §5.20 in EVALUATION_CHAPTER; Q44 in QA_PREP |
| P1.2 | **OWASP_BENCHMARK.md Two Operating Points section** + "Sifting the Noise" precedent | ✅ | arXiv:2601.22952 cited; 2-tier table added |
| P1.3 | **README restructure** — recall (91.0%) as headline; precision (96.4%) as instrument | ✅ | Two Operating Points table in Key Numbers; FPR explicitly named and explained |
| P1.4 | **EVALUATION_CHAPTER §5.20** — PR-AUC, F3, MCC, two operating points | ✅ | Full analysis section |
| P1.5 | **QA_PREP Q44** — "75.3% FPR — you scream on clean code" answer | ✅ | 3-part answer with Sifting the Noise citation |
| P2.1 | **Exploit verifier 4 → 10 categories** — SSRF, XXE, insecure-deser, open-redirect, ReDoS, LDAP | ✅ | RULE_TO_CATEGORY, PAYLOADS, SIGNALS, PARAMS, ROUTES all extended; ReDoS timing-based |
| P2.5 | **One-command full audit chain** `scripts/run_full_audit_chain.py` | ✅ | Scan → Confirmed → exploit → patch → re-exploit → sign, end-to-end |
| P3.1 | **ENGINE_MAP.md** — 36 engines classified: purpose, status, pipeline-critical | ✅ | `docs/architecture/ENGINE_MAP.md` — "why 36?" in one screen |
| P3.3 | **ADR backfill** 5 → 12 — 7 new ADRs (engine arch, confirmed tier, sandbox, taint, benchmark, remediation, adapters) | ✅ | `docs/adr/0006-0012.md` |
| P4.1 | **`--fast` CLI flag** — skips slow engines, returns Confirmed Tier in <30s | ✅ | `CORE/main.py`; sets `ACRQA_FAST_MODE=1`; documented in `--help` |

| #4 | **RealVuln benchmark** — 22/26 real multi-file Python apps cloned + scored | ✅ | ACR-QA 23.5% recall vs Bandit 18.3% (+5.2pp) on neutral third-party GT; strict CWE+line matching; §5.21 |
| #10/#13 | **Full chain verification** — all 10 exploit categories wired; 4 new fixture apps (SSRF, open-redirect, path-traversal, XXE); `TestAllTenCategoriesWired` (12 tests) | ✅ | All 10 categories: PAYLOADS+SIGNALS+PARAMS+ROUTES+RULE_TO_CATEGORY + fixture Dockerfiles |

| Recon-1 | **RealVuln triage** (a/b/c FN classification) + detectable-subset recall | ✅ | 43% FNs undetectable-by-design; det. recall 35.9% → **37.8%** after fixes |
| Recon-3 | **B307 CWE mapping fix** (eval → CWE-94, not CWE-78) + new structural rules | ✅ | 7 new rules: DEBUG=True (CWE-16), @csrf_exempt (CWE-352), mark_safe (CWE-79), cookies (CWE-1004/614) |
| Recon-4b | **Framework-structural rules** (Step 4b): CWE-16 + CWE-352 + CWE-79 + CWE-1004/614 | ✅ | SECURITY-082–088 in normalizer; rules validated |
| Recon-5 | **Three-number narrative** in REALVULN_BENCHMARK.md, QA_PREP Q45, defense framing | ✅ | "91% synthetic / 37.8% detectable / 25.1% full" — all honest, all published |

**Current best numbers (post-reconciliation):**
- ACR-QA (SecurityEval, synthetic): TPR=91.0%, FPR=75.3%, **F3=0.854**, MCC=0.210
- ACR-QA (RealVuln, detectable subset): **37.8% recall**, 90.0% precision, FPR=16.3% — leads Bandit
- ACR-QA (RealVuln, full corpus): **25.1% recall** vs Bandit 19.4% (+5.7pp) — neutral third-party
- ACR-QA (Confirmed Tier): TPR=37.1%, FPR=~0%, Precision=96.4% — auto-block operating point
- Exploit categories: **10** (up from 4)
- LLM-augmented detection: **UNION-GATED +7.4pp recall** (25.1%→32.4%) at 87.4% precision (held-out: +5.2pp, 89.5% precision)
- Exploit categories: **13** (NoSQL, GraphQL, JWT-alg-confusion added in CLI-Competitive roadmap)

---

## v10 Tracks (2026-06-04) — verified-research repositioning, honest positioning

| # | Item | Status | Result |
|---|------|--------|--------|
| P4/7.1 | **Drop false-primacy claims** — "commercially unprecedented" deleted; convergence paragraph replacing it | ✅ | README, benchmark.html, action README, PRICING all updated |
| P4/7.1 | **Competitor re-exploit table** — ACR-QA/Qualys/ZeroPath vs static-rescan incumbents | ✅ | README + PRICING_POSITIONING.md |
| P4/10.1 | **RealVuln 2026 leaderboard** in README/QA_PREP (Semgrep 17.5%, Snyk 17.4, SonarQube 6.5%) | ✅ | Verified arXiv:2604.13764; beats all rule-based tools |
| P4/10.1 | **Q48+Q49 in QA_PREP** — Qualys/ZeroPath convergence answer; RealVuln 3-number answer | ✅ | Defense answers memorizable |
| P1/3.1 | **EXPLOIT_VERIFICATION.md** expanded to 13 categories (3 Docker-live, 10 unit-tested) | ✅ | Honest status per category |
| P1/4.2 | **§5.24 in EVALUATION_CHAPTER** — competitor landscape, RealVuln leaderboard, ECE/RuleForge, fabricated-citations blacklist | ✅ | All citations web-verified 2026-06-04 |
| P3/5.1 | **Exception narrowing** in trust paths — exploit_verifier, verified_remediation, attestation | ✅ | Silent swallows replaced with logged specific exceptions |
| P0.1 | **Wheel builds clean** — `acrqa-5.0.0rc2-py3-none-any.whl` produced | ✅ | `acrqa` entry point verified |

**Current honest scores (post-v10):**
- **Installability (#1):** wheel builds ✅ · PyPI pending Ahmed's 3 manual steps → 9
- **Detection/recall (#2):** 25.1%/48% beats Semgrep 17.5%/Snyk 17.4/SonarQube 6.5% on RealVuln → 8
- **Trust wedge (#3):** 13 cats wired; 3 Docker-live; "unprecedented" dropped → 8
- **FPR/calibration (#4):** Confirmed Tier 96.4% precision; RuleForge ECE 0.17 cited → 8
- **Engineering quality (#5):** trust-path exceptions narrowed → 8.5
- **Focus (#6):** ENGINE_MAP + one-headline README → 8
- **Differentiation (#7):** convergence narrative + verified competitor table → 9
- **Traction (#8):** honestly stated as GTM runway, not faked → honest 7
- **Frontend (#9):** dist builds needed → 5 (deferred)
- **Docs/honesty (#10):** 3-number framing + §5.24 + verified cites everywhere → 9.5

---

## Suggested 25-Week Rhythm

| Weeks | Focus | Why this order |
|-------|-------|----------------|
| **1** | #1 funnel slide + #11 self-scan badge + #10 Cosign/SLSA | Quick wins. Start recruiting κ raters in parallel |
| **2–3** | #2 GHCR Docker image + #3 demo video + #4 README polish | "Installable demo" story complete |
| **4** | #5 Cloudflare Pages static dashboard | One URL to point at |
| **5–6** | #7 GitHub webhook receiver | The backend showpiece |
| **6–7** | #13 Differential SAST | Natural follow-on to webhook; "only show NEW findings" |
| **7** | #9 Multi-LLM jury + #14 Counterfactual explanations | Both are LLM prompt additions; ship together in one week |
| **8–9** | #8 VS Code extension | IDE marketplace listing |
| **10** | #6 5-rater κ analysis (raters submit by week 9) | Closes the eval gap |
| **11+** | Defense + #12 HN/LinkedIn/blog the day after | External validation |
| **12–14** | #15 Kubernetes operator with CRDs | DevOps showpiece; do after defense pressure is off |
| **15–25** | **Buffer.** Finals, job hunting, illness, serendipity (CVE discovery, paper acceptance, HN front page) | Real life never goes to plan |

---

## Why I'm NOT Doing These (deferred to "upcoming years")

These are great items but wrong-level for fresh-grad scope. They live in [`GOD_MODE_V5_PLAN.md`](archive/GOD_MODE_V5_PLAN.md) and I'll revisit them when I'm 1–3 years into industry.

### Deferred — "advanced backend/distributed-systems patterns"
- §3.6 Multi-tenancy (real RBAC + orgs)
- §3.8 gRPC sidecar
- §3.9 Event-sourced scan history
- §3.10 CQRS split

### Deferred — "platform / staff-engineer level DevOps"
- §4.9 OPA Gatekeeper integration
- §4.10 Service mesh + Vault mTLS PKI
- §4.13 PostgreSQL streaming replication + PITR
- §4.14 Cloud KMS-backed ECDSA

### Deferred — "compliance paperwork"
- §10.1–10.4 SOC 2 / ISO 27001 / NIST CSF / CIS Controls mappings

### Deferred — "academic-flex without portfolio value"
- §5.6 TLA+ formal spec
- §12.12 TLA+ quality-gate spec

### Deferred — "frontier research that takes months"
- §11.6 Federated metrics aggregation
- §11.7 ZK-proof attestation
- §11.8 Synthetic benchmark generator
- §11.10 Repository trust score with live leaderboard
- §12.9 Multi-modal AI triage
- §12.10 Full agentic remediation loop

### Deferred — "needs budget I don't have"
- §8.6 Bug bounty payouts (using free "Hall of Fame" acknowledgement-only alternative if needed)
- §9.5 Paid a11y session (using free community-volunteer alternative if needed)
- §5.4 Conference attendance (submission is free; only travel/registration is paid)

### Deferred — "good but low-priority for fresh grad"
- §3.4 GraphQL endpoint (REST is fine)
- §3.5 Plugin system
- §3.7 WebSocket (SSE is fine)
- §4.2 ArtifactHub/Terraform Registry publishing (do once #2 GHCR works)
- §7.x Product/business docs (need real users first)
- §8.x OSS community building (empty Discord is worse than no Discord)
- §11.3 Active learning (needs labelled dataset + model training pipeline — months of work)
- §11.4 Counterfactual explanations → moved to active list (#14)
- §12.2 JetBrains plugin (do after VS Code if I have time)
- §12.3 Browser extension (do after VS Code if I have time)

---

## Free Service Account Setup Checklist (Week 1)

To execute the 15 items, I need accounts on these services. All free, all no-card-required unless noted:

- [ ] **GitHub Container Registry** (`ghcr.io`) — uses existing GitHub account, free for public images
- [ ] **YouTube** — free, uses Google account
- [ ] **Cloudflare** — free tier, free Pages, free SSL, **no card required** for the free tier
- [ ] **Sigstore Cosign + Rekor** — free public-good service, no account needed
- [ ] **VS Code Marketplace publisher** — free, uses Azure DevOps account (free, no card)
- [ ] **Groq Console** — free tier already in use (existing)
- [ ] **Google AI Studio** (Gemini API) — free tier, **no card required**
- [ ] **OSF (Open Science Framework)** — free academic account for pre-registration
- [ ] **Zenodo** — free, for the DOI when I eventually upload the replication package
- [ ] **Hacker News** — free, just create account a week before defense to age it
- [ ] **LinkedIn** — already have it (presumably)

**Optional later (defer until ready):**
- [ ] **MITRE CVE Numbering Authority** — only if I find a real undisclosed vuln through X1 (§12.5)
- [ ] **HackerOne** — only if I want to submit bug bounty findings (§12.6)

---

## Success Definition for This Roadmap

The plan succeeds if, **by the end of week 11 (defense day)**:

| Floor (passing) | Target | Stretch |
|-----------------|--------|---------|
| Defense graded A | Defense A+ | A+ with commendation |
| #1–#12 shipped | #1–#14 shipped | All 15 + HN front page |
| Public GHCR image | + Cloudflare static demo URL | + VS Code Marketplace listing |
| 5-rater κ ≥ 0.78 | κ ≥ 0.85 | κ ≥ 0.90 |
| Demo video uploaded | + ≥ 100 views | + ≥ 1,000 views |
| HN post submitted | + reached front page | + top 10 |
| Resume updated with project | + 3 hiring conversations | + 1 written offer |
| — | K8s operator (#15) live | K8s operator + published blog post |

**Anything past defense day = bonus, not required.**

---

## Cadence

- **Weekly check-in:** Sunday evening — mark items 📋 → 🚧 → ✅. Move blocked items to ❓ with one-line "why blocked."
- **Mid-cycle review (week 6):** Re-read this doc. Is the 15-item list still right? Anything to add or drop?
- **Post-defense retro:** what worked, what didn't, what to revisit from `GOD_MODE_V5_PLAN.md` in the coming year.

---

## Important Rules I'm Setting for Myself

1. **No money out.** If something requires a card or threatens to bill me, I find a free alternative or skip it.
2. **No "while I'm at it" scope creep.** Each of the 15 items has a defined "done" criterion. I ship and move on.
3. **No item from "Deferred" without writing it down here first.** If something deferred starts looking tempting, I update this doc and move it into the active list, *and* move something out. The list stays at 15 or fewer.
4. **Defense day is a milestone, not a deadline.** If something slips, I have 14 weeks of buffer. I will not panic-ship anything for defense.
5. **External validation comes after technical work.** No HN post until #2–#11 are at least partially shipped. No HN post on a half-built demo.

---

## When in Doubt

- The thesis is already done. The numbers (96.4% / 100% / F1=98.2%) are real. This roadmap is about polish, validation, and adoption — not new features.
- Do the single highest-leverage thing on this list today. Don't read more plans. Don't browse more options. Do #1, then #2, then #3.
- The full ambition lives in [`GOD_MODE_V5_PLAN.md`](archive/GOD_MODE_V5_PLAN.md). When this 15-item list is fully ✅, come back, pick another lane, and repeat.

---

*Active roadmap updated 2026-06-05. All v10 tracks complete ✅. See [`GOD_MODE_V10_PERFECT_TEN_ROADMAP.md`](archive/GOD_MODE_V10_PERFECT_TEN_ROADMAP.md) for the current execution plan.*
*Strategic menu for post-defense lanes lives in [`GOD_MODE_V5_PLAN.md`](archive/GOD_MODE_V5_PLAN.md).*
