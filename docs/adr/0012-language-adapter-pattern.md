# ADR 0012 — Language Adapter Pattern: Why ABC, Why 3 Languages

**Status:** Accepted
**Date:** 2026-06-03
**Author:** Ahmed Mahmoud Abbas

---

## Context

ACR-QA supports Python, JavaScript/TypeScript, and Go via the adapter pattern in `CORE/adapters/`.
This ADR explains the design.

## Decision

Each language adapter extends `LanguageAdapter` (ABC in `CORE/adapters/base.py`). The adapter
is responsible for: detecting the language, running the appropriate tools (ruff/bandit/semgrep for
Python; ESLint/semgrep for JS; staticcheck/gosec for Go), and returning raw tool output.

The `tool_runner.py` invokes adapters; `normalizer.py` converts their output to `CanonicalFinding`.

## Rationale

**Why ABC?** Enforces the contract: every adapter must implement `detect_language()`,
`run_tools()`, and `supported_extensions()`. Adding a new language (e.g., Java) means writing one
adapter file and zero changes to the pipeline.

**Why these 3 languages?** Python is the thesis focus (most mature, most evaluated). JS/TS covers
the dominant web frontend (ESLint + Semgrep provide good coverage). Go covers cloud-native backend
services (gosec + staticcheck). Together they cover the top 3 languages in GitHub's 2025 State of
the Octoverse that have mature SAST ecosystems.

**Why not Java?** Java's SAST ecosystem (SpotBugs, SonarJava, CodeQL) has different APIs and
much larger corpora. Adding Java would require a separate adapter and evaluation set — deferred
to post-thesis.

## Consequences

- **Positive:** new languages are isolated additions; zero core engine changes needed.
- **Negative:** tool availability is platform-dependent (Go adapter requires `go` + `staticcheck`).
- **Mitigation:** adapters degrade gracefully — if a tool isn't available, the adapter logs a
  warning and returns an empty finding set (not an error).
