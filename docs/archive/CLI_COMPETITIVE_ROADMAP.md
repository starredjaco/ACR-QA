# CLI-Competitive Roadmap — Provable AppSec Testing (PAST)

> **Created:** 2026-06-04 · grounded in the 2026 SAST competitive-intelligence research
> **Positioning (the one sentence that wins):** *"We don't sell theoretical reachability or noisy alerts;
> we fire real exploits in a sandbox to cryptographically prove what's vulnerable, and re-fire the exploit
> to guarantee your AI fix actually worked."*

## The market truth (verified)

All 5 incumbents — Snyk, Semgrep, SonarQube, GHAS/CodeQL, Checkmarx — **retest statically. None
dynamically verify exploitability or verify fixes by re-exploitation.** Their #1 user complaint is
false-positive fatigue (Checkmarx ~40% FP; CodeQL users built GPT-4o tools to strip 96% of noise).
ACR-QA's exploit-verification is a genuine **blue ocean** — a new sub-category: *Provable AppSec Testing*.

**Strategy:** do NOT compete on recall (incumbents have teams + years). Win the **trust wedge**: be the
"Final Arbiter" in CI — the tool that ends the "is this real?" argument with a detonation trace.

---

## Table-stakes scorecard (the research's mandatory bar to be evaluated at all)

| Table-stakes feature (from research) | Status | Note |
|---|:---:|---|
| **Standalone CLI, no infra** | ✅ **DONE** | Fixed 2026-06-04 (was a hard Postgres crash) — commit 4332ae3 |
| **SARIF v2.1.0 emission** | ✅ **DONE** | `--sarif` standalone — commit 4aacdd0 |
| **Zero-noise GHAS upload** | ✅ **DONE** | `--sarif --confirmed-only` — commit 0097f96 |
| **Baseline SAST (seed the exploits)** | ✅ have | Bandit + Semgrep + taint + 88 custom rules |
| **Python framework depth** | ✅ have | Django/Flask/FastAPI rules; exploit-verifier covers SSTI, Pickle/PyYAML deser, SQLi, cmd-inj, path, SSRF, XXE, ReDoS, LDAP, open-redirect (10 cats) |
| **<5-minute feedback** | 🟡 verify | Static scan ~4s/57 files ✅. *Must confirm the full exploit-verify + sandbox chain stays <5 min* (Docker-gated). |
| **PR-workflow decoration** | 🟡 partial | `acrqa-action/` exists; `scripts/post_pr_comments.py` exists — needs to surface *verified-exploit* results + verified fix in the PR |
| **`pip install acrqa`** | ❌ **BLOCKER** | Not on PyPI ("No matching distribution"). The literal day-one barrier. Release task (needs PyPI trusted publisher). |
| **Action sells the wedge** | ❌ | `action.yml` still says "10 analysers + RAG" — not exploit-verification/attestation |

---

## Prioritized roadmap

### P0 — Reachability of the wedge (do first; cheap; unblocks everything)
1. **Publish to PyPI** so `pip install acrqa` works. *Nothing else matters if nobody can install it.*
   Needs the PyPI trusted-publisher setup (already noted in thesis tasks). **DoD:** `pip install acrqa && acrqa --help`.
2. **Rewrite `acrqa-action/action.yml` + README** around the wedge: "exploit-proven findings, verified
   remediation, attested SARIF" — not "10 analysers." **DoD:** action description leads with PAST.
3. **Verify the <5-min rule** end-to-end on a real repo with Docker up (scan → exploit-verify →
   Confirmed Tier → SARIF). **DoD:** published timing; if >5 min, add a `--fast` exploit budget.

### P1 — Make the wedge undeniable in the PR (the demo that sells)
4. **PR decoration with the detonation trace.** When a finding is exploit-verified, the PR comment shows
   the actual PoC request/response + the Confirmed badge + (if `--fix`) the re-exploit-failed proof.
   This is the "ends the argument" moment. **DoD:** a PR comment with a real verified-exploit trace.
5. **One-command verified-remediation in CI** (`scan → exploit → fix → re-exploit-fails → sign → SARIF`),
   gated so only verified fixes are proposed. **DoD:** GitHub Action job that posts a verified fix.

### P2 — Economics & trust packaging (the switch triggers)
6. **A pricing/positioning page** that contrasts with incumbent pain: no LOC penalty (SonarQube), no
   90-day committer bloat (GHAS), no 4.2× "Valley of Pain" (Snyk). Metric: "per verified exploit" or
   flat per-core-contributor. **DoD:** `docs/PRICING_POSITIONING.md` (positioning, not a real billing system).
7. **Evidence-pack polish** — the ECDSA + Rekor attested chain as a downloadable audit artifact
   (`scripts/generate_evidence_pack.py` exists). **DoD:** one-command signed evidence bundle.

### P3 — Depth-over-breadth credibility (the research's #3 adoption rule)
8. **Exhaustive Python exploit depth** — harden the 10 categories, add the highest-value missing ones
   (NoSQL injection, GraphQL, JWT-alg-confusion). **DoD:** each a passing sandbox exploit test.
9. **DefectDojo / ASPM ingestion** — SARIF already enables this; document the integration. **DoD:** a
   tested DefectDojo import path.

> **Explicitly NOT now:** language breadth (Java/C#/Go beyond what exists), a proprietary dashboard war,
> chasing incumbent recall. Depth in Python + the trust wedge is the winning focus.

---

## What I recommend (honest)

For a **thesis**, you're already there: a working PAST tool with table-stakes met is a strong, defensible,
genuinely-novel contribution. **Ship P0 (install + action + timing), prep the demo, defend.**

For a **product** ("compete from day one"), the order is: **P0 → P1**. Installable + a PR that shows a
real detonation trace is the entire pitch. Everything else (P2/P3) is post-validation. Do **not** build
P3 before P0 — an uninstallable tool with deep exploits helps no one.

The wedge is real and the incumbents structurally can't follow (their architecture is static). Your job
isn't to out-feature them — it's to make the one thing they can't do **trivially reachable and
visibly undeniable** in a pull request.
