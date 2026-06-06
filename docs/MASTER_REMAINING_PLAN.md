# ACR-QA — Master Remaining Items Plan
> **Created:** 2026-06-06 · **Purpose:** Single consolidated view of everything left undone across all existing plans,
> plus the new benchmark-strengthening items identified in the head-to-head analysis.
> **Defense date:** 2026-06-25 — ~19 days from now.
> **Rule:** If it's not in this file, it doesn't exist. This supersedes all per-plan scattered TODOs.

---

## 🔴 SECTION 1 — New: Benchmark Strengthening (head-to-head gaps)

*Items identified 2026-06-06 from the head-to-head results analysis.*

| # | Item | Effort | Priority | Why |
|---|------|--------|----------|-----|
| N1 | **Add CodeQL to the head-to-head table** | 2–3 days | HIGH | CodeQL is the gold-standard academic baseline. Your table has Bandit + Semgrep — adding CodeQL makes the comparison unambiguous and more credible. Run it against the same 8-CVE recall corpus + precision corpus, add a `codeql-*.json` results file, and update `head_to_head_benchmark.json`. |
| N2 | **Add an "Exploit Verification" column to the comparison table** | ½ day | HIGH | This is your unique dimension. Neither Bandit, Semgrep, nor CodeQL can say whether a finding is *actually* exploitable. A column `exploit_verified: Yes / No / Partial` makes ACR-QA the only `Yes` — no argument needed. Update `HEAD_TO_HEAD_CHART.html` + thesis table. |
| N3 | **Explicitly state why Snyk/Checkmarx are excluded** | ½ day | MEDIUM | Add a one-paragraph justification in the thesis and in `head_to_head_benchmark.json` notes: commercial license, API-key gated, non-reproducible results. This kills the "why didn't you compare with Snyk?" examiner question. |
| N4 | **Re-run precision numbers after SonarCloud gate passes** | 1 day | HIGH | Coverage is 65.5% against an 80% gate. Once the Postgres service is added to the Sonar workflow (current in-progress commit), re-run and capture the final coverage number for the thesis. |

---

## 🟡 SECTION 2 — From ACTIVE_ROADMAP.md (items NOT yet ✅)

| # | Item | From roadmap # | Status | Notes |
|---|------|----------------|--------|-------|
| A1 | **5-min demo video on YouTube** | #3 | 📋 Ahmed records | Script at `docs/DEMO_VIDEO_SCRIPT.md`. Agent can't do this — Ahmed must record. |
| A2 | **Free service accounts setup** (GitHub Container Registry, YouTube, Cloudflare, VS Code Marketplace) | Checklist | ❓ | Most are tick-boxes Ahmed needs to complete manually. |

---

## 🟡 SECTION 3 — From GOD_MODE_V10_PERFECT_TEN_ROADMAP.md (incomplete items)

| # | Item | Phase | Status | Notes |
|---|------|-------|--------|-------|
| V1 | **PyPI Trusted Publisher setup + publish** | P0 #1.2–1.3 | ❌ BLOCKER | `pip install acrqa` still fails. Ahmed needs to create the PyPI project + OIDC publisher. Claude can prepare the `pyproject.toml` packaging config; Ahmed does the manual PyPI step. |
| V2 | **Frontend `dist` build + a11y pass + deploy proof** | P3 #9.1 | ❌ Partial (5/10) | `FRONTEND/` exists but no confirmed local `dist` build. Deferred in v10 honestly. May be skipped for defense. |

---

## 🟡 SECTION 4 — From CLI_COMPETITIVE_ROADMAP.md (incomplete items)

| # | Item | Phase | Status | Notes |
|---|------|-------|--------|-------|
| C1 | **Verify the `<5-min` end-to-end timing rule** | P0 #3 | 🟡 Unverified | Static scan is ~4s. The full exploit-verify + sandbox chain timing is unconfirmed. Must test on a real repo with Docker up. If >5 min, add `--fast` exploit budget. |
| C2 | **PR decoration showing the detonation trace** | P1 #4 | ❌ Not done | PR comment showing actual PoC request/response + Confirmed badge. The "ends the argument" demo moment. High thesis value. |
| C3 | **Rewrite `acrqa-action/action.yml` + README around the wedge** | P0 #2 | ❌ Still says "10 analysers" | Replace with "exploit-proven findings, verified remediation, attested SARIF." One-liner fix. |
| C4 | **DefectDojo / ASPM ingestion documentation** | P3 #9 | ❌ Not done | SARIF already enables it — just needs a tested import path documented. Low effort, good thesis integration story. |

---

## 🟡 SECTION 5 — From GO_BIG_LLM_DETECTION_PLAN.md (incomplete items)

| # | Item | Phase | Status | Notes |
|---|------|-------|--------|-------|
| L1 | **Full-corpus re-run with LLM-augmented pipeline** | Phase 3 | ❌ Not done | Phase 1+2 shipped (held-out GO: +5.2pp recall). Full RealVuln + SecurityEval re-benchmark with the wired `llm_detector.py` pipeline not yet re-run. |
| L2 | **Update README + QA_PREP with LLM-augmented numbers** | Phase 3 | ❌ Partial | The numbers from the held-out test (32.4% recall / 89.5% precision) are not yet the headlines. `README.md` and `QA_PREP.md` still show pre-LLM numbers in places. |

---

## 🟡 SECTION 6 — From REALVULN_RECONCILIATION_PLAN.md (incomplete items)

> All core steps (1–5) have been executed and documented. The following optional/follow-up items remain.

| # | Item | Step | Status | Notes |
|---|------|------|--------|-------|
| R1 | **Optional Step 4 — close genuine detectable gaps from bucket (b)** | Step 4 | ❌ Optional | Only needed if detectable recall is still weak. Guarded: add rules only with held-out validation. Current detectable recall is 37.8% — may be good enough for defense. |
| R2 | **Future Work section on semantic authorization / IDOR (CWE-862/639)** | Future Work | ❌ Not written | A thesis section explaining the architectural boundary: static analysis ends at intent; IDOR needs LLM-hybrid at 23–65% precision, scoped as future work. High thesis quality signal — shows you know what you can't do. |

---

## 🟢 SECTION 7 — CI/CD / SonarCloud (in-progress right now)

| # | Item | Status | Notes |
|---|------|--------|-------|
| S1 | **SonarCloud Quality Gate: 3 failing conditions** | 🚧 In progress | Coverage 65.5% (needs ≥80%), E Security Rating (path traversal blocker), 29 Security Hotspots. The current commit adds Postgres service to `sonar.yml` — awaiting CI result. |
| S2 | **Tests / Run Test Suite** | ✅ Passing | 81%+ coverage with DB-backed integration tests. |
| S3 | **Commit pre-commit hook pass** | 🚧 In progress | Commit `fix(ci): spin up Postgres...` running smoke tests now. |

---

## 📋 SECTION 8 — Priority Order for Remaining Days (19 days to defense)

| Order | Item(s) | Effort | Owner |
|-------|---------|--------|-------|
| 1st | **S1** — Wait for SonarCloud gate to pass with new Postgres workflow | — | CI auto |
| 2nd | **N2** — Add exploit-verification column to comparison table | ½ day | Claude |
| 3rd | **C3** — Rewrite `acrqa-action` description to lead with the wedge | 1h | Claude |
| 4th | **N1** — Add CodeQL to head-to-head (run it, record results) | 2–3 days | Claude + Ahmed |
| 5th | **L1+L2** — Full-corpus LLM-augmented re-benchmark + update README/QA_PREP | 1 day | Claude |
| 6th | **R2** — Write Future Work: semantic authorization thesis section | ½ day | Claude |
| 7th | **C1** — Verify <5-min end-to-end timing | ½ day | Claude + Ahmed (Docker) |
| 8th | **N3** — Snyk/Checkmarx exclusion justification in thesis | ½ day | Claude |
| 9th | **V1** — PyPI publish setup | Ahmed manual | Ahmed |
| 10th | **A1** — Demo video | Ahmed manual | Ahmed |
| 11th | **C2** — PR detonation trace decoration | 2–3 days | Claude (post-defense optional) |
| 12th | **V2** — Frontend dist build | Deferred | Post-defense |

---

## 🚫 Explicitly NOT Doing (confirmed deferrals)

These were in old plans but are correctly deferred — do not re-open:

- Multi-tenancy RBAC, gRPC sidecar, CQRS (staff-engineer level)
- OPA Gatekeeper, Vault mTLS, Postgres streaming replication
- SOC 2 / ISO 27001 compliance paperwork
- TLA+ formal spec
- Federated metrics, ZK-proof attestation, synthetic benchmark generator
- MicroVM sandboxing (Firecracker/gVisor) — tagged as v10 P5
- Stripe / SaaS billing — tagged as v10 P5
- JetBrains / Browser extensions
- Kubernetes operator (already ✅ built — just deployment is Ahmed's job)

---

## ✅ Quick Reference: What's Already Done (don't re-do)

- All v10 tracks ✅
- All v9 tracks ✅ (PR curve, F3, MCC, 10→13 exploit categories, RealVuln reconciliation)
- All v8 tracks ✅ (OWASP benchmark, Verified Remediation Engine)
- All v7 tracks ✅ (86 custom rules, 91% SecurityEval recall)
- All v6 Phase 0–3 ✅ (Trust layer, Confirmed Tier, APIs, GitHub Action gate)
- `ACTIVE_ROADMAP.md` items #1–#2, #4–#15 all ✅
- Path traversal blocker resolved in `verified_remediation.py` ✅
- Insecure `/tmp` file writes removed from `main.py` ✅
- NoSQL / GraphQL / JWT-alg confusion exploit categories wired ✅
- LLM-augmented detection: held-out GO, +5.2pp recall shipped ✅

---

*Last updated: 2026-06-06. Everything in Sections 2–6 that is not explicitly ✅ in the roadmaps is genuinely remaining.*
