# ACR-QA Pricing & Positioning — Provable AppSec Testing (PAST)

> **Positioning:** *"We don't sell noisy alerts; we fire real exploits to prove what's vulnerable,
> and re-fire the exploit to prove your fix actually worked."*
>
> **Category:** Provable AppSec Testing (PAST) — exploit-verified remediation for first-party
> application source code, in CI, ECDSA-attested, at $0.
>
> **Honest positioning (2026):** Exploit-verified remediation is now the 2026 vanguard. Qualys
> TruConfirm/Agent Val (Feb–Mar 2026) re-detonates CVEs on deployed infrastructure. ZeroPath ships
> AI-native SAST+DAST with fix verification (closed-source). VulnRepairEval (arXiv:2509.03331) and
> PatchEval (arXiv:2511.11019) institutionalized it academically. ACR-QA **independently converges**
> for first-party SAST in CI — the open, developer-facing, $0 version. Convergence validates the
> paradigm; differentiation is the layer (CI-native / first-party / open / attested).

---

## Market Map — Who Does Re-Exploit-to-Verify-Fix

| Tool | Layer | Re-exploit fix verify | Open | Notes |
|---|---|:---:|:---:|---|
| **ACR-QA** | First-party SAST in CI | ✅ | ✅ | $0, ECDSA, 13 exploit categories |
| Qualys TruConfirm | CVE/deployed ETM | ✅ | ❌ | Deployed infra only, Mar 2026 |
| ZeroPath | AI-native SAST+DAST | ✅ | ❌ | Closed source |
| Snyk / Semgrep / GHAS | Traditional SAST | ❌ | varies | Static re-scan only |

## Why Traditional Incumbents Still Lose

| Pain point (verified research) | Incumbent | ACR-QA |
|---|---|---|
| 30–40% false positives | Snyk, Checkmarx, CodeQL | **0%** on Confirmed Tier (exploit-proven) |
| "Is this real?" argument in PRs | All traditional | Detonation trace in the PR comment |
| Static retest only (guesses if fix worked) | Snyk, Semgrep, GHAS | Re-exploit proves the fix killed the vuln |
| Per-LOC pricing grows with AI code | SonarQube | Flat per-core-contributor |
| 90-day committer bloat | GitHub Advanced Security | N/A |
| No cryptographic audit trail | All | ECDSA-P256 + Sigstore Rekor (tamper-evident) |
| RealVuln recall (real apps, 2026 benchmark) | Semgrep 17.5% / Snyk 17.4 / SonarQube 6.5% | **ACR-QA 25.1%** (beats all rule-based tools) |

---

## Pricing Philosophy (the switch triggers from research)

### What kills Snyk: the "Valley of Pain"

Snyk's SCA pricing scales with repos × severity. A 100-repo org with active AI coding
(1.88× more flaws per codebase) pays a 4.2× "Valley of Pain" — the moment they reach
the tier where every flagged dependency costs money. ACR-QA never charges per finding.

### What kills SonarQube: LOC pricing in the AI era

SonarQube charges by lines of code. GitHub Copilot generates 30–50% of code at AI shops.
Paying for AI-generated lines while AI *introduces* bugs is a double penalty.

### What kills CodeQL/GHAS: "96% noise" problem

A GitHub Advanced Security user reported building a GPT-4o tool to strip 96% of CodeQL
alerts before engineers saw them. The tool they pay for is so noisy they need another AI
to clean it. ACR-QA's Confirmed Tier has 96.4% precision — they're paying for signal,
not noise + cleanup.

---

## Proposed Tiers

### Open Source / Research — $0

- Full Bandit + Semgrep + 88 custom rules
- LLM-augmented detection (`--llm`)
- SARIF v2.1.0 export
- Confirmed Tier (pattern-based)
- **Not included:** exploit-verification sandbox, ECDSA attestation, Rekor logging

### Professional — per core-contributor / month

- Everything in Open Source
- **Exploit-verification** (10 categories: SQLi, CMDi, SSTI, path-traversal, SSRF, XXE,
  insecure-deser, open-redirect, ReDoS, LDAP-injection)
- **Verified Remediation** — re-exploit proves the fix worked
- **ECDSA-signed attestation** + Sigstore Rekor transparency log
- PR decoration with detonation traces
- Evidence pack for SOC2/ISO27001/EU CRA auditors

### Enterprise — custom

- Everything in Professional
- Multi-repo fleet scanning
- ASPM ingestion (DefectDojo, Jira, etc.)
- Custom exploit categories (NoSQL injection, GraphQL, JWT-alg-confusion)
- SLA + dedicated support

---

## The Pitch (30 seconds)

> "When CodeQL flags 400 issues and engineers stop looking, that's not security — that's alert
> fatigue theater. ACR-QA doesn't flag; it proves. For each HIGH finding, we spin up a Docker
> sandbox, fire a real PoC, and capture the response. If the exploit fires, you get a detonation
> trace in your PR — not a suggestion that it might be exploitable, proof that it is. And when
> your AI generates a fix, we re-fire the exploit on the patched code to prove it actually closed
> the hole — then sign the chain with ECDSA. That's what we mean by Provable AppSec Testing."

---

## Competitor Contrast Table (for sales conversations)

| Feature | Snyk Code | Semgrep | CodeQL/GHAS | **ACR-QA** |
|---|:---:|:---:|:---:|:---:|
| Exploit verification (dynamic) | ❌ | ❌ | ❌ | ✅ 10 categories |
| Verified remediation (re-exploit) | ❌ | ❌ | ❌ | ✅ ECDSA-signed |
| Cryptographic scan attestation | ❌ | ❌ | ❌ | ✅ Rekor |
| SARIF merge-blocking (precision) | ❌ | partial | partial | ✅ 96.4% precision |
| PR detonation trace | ❌ | ❌ | ❌ | ✅ PoC + response |
| LLM-augmented recall | ❌ | ❌ | ❌ | ✅ +7.4pp, gated |
| Pricing model | per-dev + severity | per-dev | per-committer | per-core-contributor |
| LOC penalty | ❌ | ❌ | ✅ LOC-based | ❌ (flat) |

---

## Evidence Pack (for auditors)

```bash
# Generate a signed evidence bundle for SOC2/ISO27001/EU CRA
python3 scripts/generate_evidence_pack.py --run-id <run_id> --output evidence.zip
```

The bundle contains:
- ECDSA-P256 signed scan verdict
- Sigstore Rekor transparency log index
- Per-finding exploit proof (payload + response)
- Verified fix diffs + re-exploit failure proof
- SARIF v2.1.0 (confirmed findings only)

**For auditors:** this is evidence that a security review happened AND that every flagged item
was proven exploitable — not just "a scanner ran and here's what it guessed."
