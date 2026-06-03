# ADR 0009 — Taint Analysis: HTTP-Source Confirmation, 5-Line Window

**Status:** Accepted
**Date:** 2026-06-03
**Author:** Ahmed Mahmoud Abbas

---

## Context

ACR-QA's `taint_analyzer.py` gates findings on HTTP-source taint confirmation.
This ADR explains the design choices and their limitations.

## Decision

**Sources:** `request.args.get`, `request.form.get`, `request.json`, `request.data`,
`request.headers.get`, `request.cookies.get`, and their async equivalents.

**Sinks:** `cursor.execute`, `subprocess.run`, `os.system`, `eval`, `exec`, `open` with
user-controlled path, and ~20 others (see `config/taint_sinks.yml`).

**Window:** ±5 lines from the flagged line. A finding is taint-confirmed if a source appears
within ±5 lines of the sink, or if the variable name at the sink matches a known-tainted name
from a source on a previous line in the same function.

**Sanitizers:** functions in `config/taint_sanitizers.yml` break the taint chain.

## Rationale

**Why HTTP-source only?** The thesis focuses on web-application vulnerabilities where the attacker
controls HTTP input. File-read, env-var, and database-sourced taint are tracked but weighted
lower — they have separate sources and often reflect internal data, not attacker-controlled data.

**Why ±5 lines?** A narrower window (±2) misses multi-line assignments common in Flask/Django
route handlers. A wider window (±20) has unacceptable false-positive rate on large files.

**Known limitation:** inter-procedural taint (tracking data across function call boundaries) is
implemented but approximate. Deep call chains may miss taint or propagate it incorrectly.
Rice's theorem guarantees no complete solution; this is an explicit scope limitation (see ADR 0001).

## Consequences

- **Positive:** dramatically reduces false positives in clean library code (expected by design).
- **Negative:** may miss true positives where the data flow crosses function boundaries.
- **Mitigation:** the full output exposes all findings (no taint gate); the Confirmed Tier applies
  the gate only to the precision stratum.
