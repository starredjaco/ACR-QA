# ADR 0011 — Verified Remediation: Re-Exploit Instead of Re-Scan

**Status:** Accepted
**Date:** 2026-06-03
**Author:** Ahmed Mahmoud Abbas

---

## Context

ACR-QA's Verified Remediation engine (`CORE/engines/verified_remediation.py`) re-runs the exploit
after applying an AI-generated fix, instead of doing a static re-scan. This ADR explains why.

## Decision

**Pipeline:** detect → exploit-fires (ExploitVerifier, `verified-exploitable`) → AI patch
(AutoFixEngine) → apply in sandbox copy → re-run same payload (ExploitVerifier) → if
`verified-unexploitable` → `fix_verified=True` → ECDSA-sign `(vuln_proof, fix_diff, fix_proof)`.

## Rationale

**Why re-exploit instead of re-scan?**

Static re-scan (Snyk's method, claimed ~80% accuracy) has a fundamental limitation: it checks
whether the pattern that flagged the finding is gone, not whether the actual exploit still works.
A fix that changes variable names but preserves the data flow will pass a static re-scan but
fail a live exploit. ACR-QA's re-exploit approach is binary ground truth: the payload either
fires or it doesn't.

**Academic alignment:** VulnRepairEval (arXiv:2509.03331, Sept 2025) uses containerized
differential verification — the exploit fires on the vulnerable container and fails on the patched
container. CVE-Bench (ICML'25, arXiv:2503.17332) evaluates fix quality by exploiting 40 real CVEs.
ACR-QA brings this exploit-based evaluation paradigm into an integrated, production-shaped tool.

**Why sign the triple?** An auditor gets tamper-evident proof: "this exploit worked before the
patch, this patch was applied, this exploit now fails." Not "the scanner ran" — "the fix closes
the exploit, provably." This is the SOC2/ISO27001 audit value proposition.

## Consequences

- **Positive:** ground-truth fix verification; audit-grade signed evidence chain.
- **Negative:** requires Docker; LLM-generated patches vary in quality; fix_verified=True rate
  depends on AutoFixEngine coverage and LLM patch quality.
- **Scope:** only covers web-injectable categories (10 categories as of 2026-06-03). Logic bugs,
  crypto flaws, and auth issues cannot be Docker-re-exploited and are out of scope.
