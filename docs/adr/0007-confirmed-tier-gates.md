# ADR 0007 — Confirmed Tier: Why Exactly Four Gates

**Status:** Accepted
**Date:** 2026-06-03
**Author:** Ahmed Mahmoud Abbas

---

## Context

The Confirmed Tier (96.4% precision, CI [90.9%, 100%]) uses exactly four orthogonal gates.
This ADR explains why four, and why these four.

## Decision

Gate 1 — **Severity: HIGH only.**
Gate 2 — **Rule set: 22 curated rules** (empirically ≥80% precision on the 30-repo corpus).
Gate 3 — **Production code path** (excludes test/, migration/, vendor/, docs/ directories).
Gate 4 — **Bandit `issue_confidence == HIGH`** (Bandit's AST-shape confidence, independent of severity).

## Rationale

Each gate is *independent* — they catch different false-positive patterns:
- Gate 1 alone: precision ~25% (HIGH findings still have many FPs in clean library code)
- Gate 2 alone: precision ~35% (rule precision varies; some HIGH-precision rules catch ~80%)
- Gate 3 alone: removes non-production noise (test asserts, migration SQL, vendored code)
- Gate 4 alone: Bandit's confidence is AST-based; HIGH means the pattern unambiguously matches

All four together: 55 findings at 96.4% precision — a stratum safe for automated merge-blocking.

The 22-rule set was chosen by empirical analysis: each rule was evaluated on the 30-repo
production corpus; only rules with ≥80% observed precision were included.

## Consequences

- **Positive:** highly defensible to an examiner — each gate has an independent rationale.
- **Positive:** low recall (by design) — only ~30% TPR on synthetic corpora, but near-zero FPR
  on production code. This is the correct trade-off for an auto-block gate.
- **Negative:** misses true positives that don't satisfy all four gates. Mitigated by also
  exposing the full output (91.0% recall) for human triage.
