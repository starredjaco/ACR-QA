# ADR 0006 — Detection Engine Architecture: Why 36 Engines

**Status:** Accepted
**Date:** 2026-06-03
**Author:** Ahmed Mahmoud Abbas

---

## Context

ACR-QA has 36 engine files in `CORE/engines/`. This reads as sprawl to a staff engineer who
opens the directory for the first time. This ADR explains why the count is intentional and how
the engines are organised.

## Decision

Engines are classified into five roles (see `docs/architecture/ENGINE_MAP.md`):
1. **Core pipeline** (6) — always run; form the CanonicalFinding → score → gate chain
2. **Detection + verification** (5) — find and prove vulnerabilities (exploit, attest, autofix)
3. **Opt-in features** (12) — flag-activated or file-presence-activated
4. **Evaluation / research** (10) — benchmarks, API endpoints, academic study
5. **External adapters** (2) — Trivy and TruffleHog wrappers

The 11 pipeline + detection engines are what run on every scan. The other 25 engines are
opt-in or eval-only and do not affect default scan latency.

## Rationale

Each engine corresponds to a published technique or a thesis contribution:
- `exploit_verifier.py` + `verified_remediation.py` → the novel contribution (VulnRepairEval-class AVR)
- `taint_analyzer.py` → inter-procedural HTTP-source taint (PLDI-era technique)
- `confirmed_tier.py` → the precision instrument (4-gate stratum, 96.4% precision)
- `attestation.py` → ECDSA + Sigstore provenance (SLSA L3)
- Adapter engines → normalize third-party tools without coupling the pipeline to their schemas

Alternatives considered: a single monolithic engine (rejected — untestable), engine plugins
(rejected — over-engineering for a thesis), fewer engines by merging roles (rejected — merging
attestation with normalizer would violate single-responsibility and make the data contract opaque).

## Consequences

- **Positive:** each engine is independently testable; the CanonicalFinding contract is the only
  coupling point; new tools/categories are added by writing a new adapter, not modifying existing code.
- **Negative:** cold-start cognitive load is high. Mitigated by `ENGINE_MAP.md` and this ADR.
- **Maintenance:** bus-factor-1 risk. Mitigated by docstrings, per-engine tests, and the canonical
  schema documentation.
