# ADR-001: Intra-Procedural Taint Analyzer (Phase 1 MVP)

**Status:** Accepted
**Date:** 2026-05-14
**Deciders:** Ahmed Abbas (thesis author)

---

## Context

ACR-QA's Semgrep and Bandit rules detect surface-level vulnerabilities (eval, shell injection, hardcoded secrets) but miss flows where user input travels through intermediate variables before reaching a dangerous sink. For example:

```python
raw = request.form["q"]      # Bandit/Semgrep: not flagged (just an assignment)
cleaned = raw.strip()        # taint propagates — still unsafe
cursor.execute("SELECT " + cleaned)  # sink — but no tool connects it to the source
```

Adding a taint-flow engine closes this gap without requiring an external tool or inter-procedural analysis infrastructure.

## Decision

Implement an **intra-procedural** (single-function scope) AST-based taint analyzer as `CORE/engines/taint_analyzer.py`, wired into the pipeline after deduplication and before the reachability engine.

### Scope (MVP)

**Sources (5):** `request.args`, `request.form`, `request.json`, `request.cookies`, `os.environ`

**Sinks (3):** `execute()` → SECURITY-027 (SQL injection), `eval()` → SECURITY-001 (code injection), `subprocess.*` → SECURITY-021 (OS command injection)

**Propagation tracked:** direct assignment, method calls on tainted base, f-strings, string concatenation (`+`, `%`), subscript access, `str()`/`encode()` wrappers.

**Not in MVP scope:** cross-function taint tracking, sanitizer awareness, class-level state propagation.

### Architecture

```
TaintAnalyzer.enrich_findings(findings, target_dir)
  └── analyze_directory(target_dir)
        └── analyze_file(filepath)
              └── per FunctionDef: _FunctionTaintVisitor
                    ├── visit_Assign  → track tainted variables
                    ├── visit_Call    → check if tainted arg reaches sink
                    └── _propagate   → resolve taint through expressions
```

Each function gets a **fresh `_FunctionTaintVisitor`** with its own `_tainted: dict[str, TaintInfo]` — this enforces intra-procedural isolation.

Confidence scoring: `max(0.4, 0.95 - 0.1 * (hops - 1))` — starts at 0.95 for direct 1-hop flows, decays with each propagation step, floors at 0.4.

### Config-driven sources and sinks

`config/taint_sources.yml` and `config/taint_sinks.yml` define sources and sinks declaratively so they can be extended without code changes.

### Database

Migration `0007` adds three nullable columns to `findings`:
- `taint_source TEXT` — e.g. `"request.args"`
- `taint_path JSONB` — ordered list of propagation steps
- `taint_confidence REAL` — 0.0–1.0 confidence score

## Consequences

**Positive:**
- Detects multi-hop injection flows that pattern-matching tools miss
- Config-driven — sources/sinks extensible without code changes
- Zero dependencies beyond stdlib `ast` and `yaml`
- Graceful degradation in pipeline (`try/except` wrapper)

**Negative / deferred:**
- Intra-procedural only — misses flows that cross function boundaries (cross-function taint deferred to post-defense)
- No sanitizer recognition — parameterized queries still flagged (acceptable for MVP; precision tradeoff documented)
- Python-only (JS/Go taint deferred)

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| Use Semgrep taint mode | Requires semgrep Pro / `taint: true` rules; adds external dependency |
| Use CodeQL | Too heavy for self-hosted thesis deployment |
| Cross-function taint (full) | Requires call-graph resolution; scope exceeds MVP timeline |
