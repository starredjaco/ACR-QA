# ACR-QA Threat Model — Honest Scope & Limitations

_T4.6 — Threat-model honesty document for thesis defence._

This document states what ACR-QA is designed to detect, what it explicitly does NOT
cover, and why. Honest scope boundaries are as important as capability claims in
academic security tooling.

---

## What ACR-QA Detects

ACR-QA is a **static analysis aggregation platform** for Python, JavaScript, and Go
repositories. It aggregates 7 tools (Bandit, Semgrep, Ruff, Radon, Vulture, CBOM,
ESLint) and adds an inter-procedural taint analysis layer.

### Covered vulnerability classes

| Class | CWE | Tools |
|-------|-----|-------|
| Injection (SQL, shell, eval, exec) | CWE-78, CWE-89 | Bandit, Semgrep, taint_analyzer |
| Insecure deserialization (pickle, YAML unsafe) | CWE-502 | Bandit, Semgrep |
| Weak cryptography (MD5, SHA1, weak modes) | CWE-327, CWE-338 | CBOM, Bandit |
| Hardcoded secrets | CWE-798 | Semgrep, Bandit (B105/B106/B107) |
| Path traversal | CWE-22 | Semgrep |
| XML/HTML injection, XXE | CWE-611, CWE-79 | Semgrep |
| SSRF | CWE-918 | Semgrep (SECURITY-046) |
| Template injection (SSTI) | CWE-1336 | Semgrep |
| Dead code / complexity (quality) | — | Radon, Vulture, Ruff |
| Supply-chain (SBOM, outdated deps) | CWE-1104 | CBOM |

### Recall results (Track 1 + Track 2)

- **11/11 statically-detectable CVEs detected** (100% recall on detectable subset)
- **2 honest misses** — not detectable by pattern-based static analysis (see below)

---

## What ACR-QA Does NOT Detect — and Why

### 1. ORM-internal vulnerabilities (honest miss category)

**Example**: CVE-2024-36039 (PyMySQL key escaping), CVE-2024-42005 (Django ORM column alias)

**Why not detectable**: The vulnerable logic is inside ORM library internals. The
application call site contains no detectable pattern — a developer calls
`connection.execute(query)` correctly, but the library's internal SQL construction
is flawed. Detecting this requires:
- Full inter-procedural taint analysis across library boundaries, OR
- Semantic understanding of ORM-internal SQL construction

Neither pattern-based nor shallow-taint tools can detect these. This is a documented
limitation of static analysis as a technique, not a bug in ACR-QA.

**Coverage gap**: ~5–10% of CVEs in the Python ecosystem are ORM/framework-internal.

### 2. Logic bugs and business-logic vulnerabilities

**Why not detectable**: ACR-QA detects structural patterns (dangerous function calls,
taint flows). Business logic errors — authorisation bypasses, time-of-check/time-of-use
races, incorrect permission checks — have no syntactic pattern to match.

**What would be needed**: Formal verification, symbolic execution, or manual review.

### 3. Memory-safety vulnerabilities in native extensions

**Why not detectable**: Python/JS vulnerability classes. Buffer overflows, UAF, and
memory corruption occur in C extensions (e.g. NumPy, Pillow's C layer). ACR-QA scans
Python/JS/Go source, not native extension C/C++ code.

**Scope boundary**: ACR-QA covers the interpreted language layer only. Pillow CVE-2024-3219
(which ACR-QA DOES detect) was caught at the Python call-site level, not in the C layer.

### 4. Runtime-only vulnerabilities

**Why not detectable**: Some vulnerabilities only manifest at runtime:
- Race conditions depending on timing
- Vulnerabilities requiring specific runtime state (e.g. session fixation via complex
  auth flow)
- Server-side request forgery to internal services (SSRF) where the internal network
  topology is unknown at scan time

**Exception**: ACR-QA's SSRF rule (SECURITY-046) detects structural SSRF patterns.
Runtime-specific SSRF (where the danger depends on which internal hosts exist) is not
covered.

### 5. Zero-day vulnerabilities in well-known safe patterns

**Why not detectable**: Semgrep and Bandit rules match known-bad patterns. A novel
vulnerability class with no existing rule will be missed. ACR-QA's rule base is
updated via semgrep community rules + custom SECURITY-* rules; it does not
synthesise new detection logic.

### 6. Encrypted/obfuscated code

**Why not detectable**: Tools operate on source AST. Obfuscated JS (minified,
packed, webpack bundles without source maps) and compiled Python (`.pyc` only)
are not analysed.

---

## Precision vs. Recall Trade-offs

| Trade-off | ACR-QA's position |
|-----------|------------------|
| Precision vs. recall | Prefers **recall** (lower FP threshold) for security rules; quality rules are filtered by severity tier |
| Triage burden | Reduced via security-tier stratification (219 of 630 H/M findings reach analysts) |
| False-negative risk | Documented honest misses; 100% recall on detectable CVE classes |
| Reachability demotion | UNREACHABLE findings demoted, not suppressed — remain visible at LOW severity |

---

## Attack Surface NOT Covered

| Attack surface | Coverage |
|---------------|----------|
| SAST (Python/JS/Go source) | ✓ Covered |
| SCA (dependency vulnerabilities) | Partial — CBOM detects crypto misuse in deps; OSV/NVD CVE matching not implemented |
| DAST (runtime testing) | ✗ Not covered — out of scope for static analysis thesis |
| Secret scanning (committed secrets) | ✓ Covered via Semgrep secret rules + Bandit B105/B106 |
| IaC misconfiguration (Terraform, Helm) | Partial — Helm chart present but IaC scanner scope limited |
| Container image scanning | ✗ Not covered — Trivy adapter stub exists but not wired to scoring |
| Binary / compiled artefacts | ✗ Not covered |

---

## Comparison with Full-Spectrum Tools

ACR-QA is not a replacement for enterprise SAST platforms. It is a research platform
demonstrating the value of the aggregation + provenance layer:

| Capability | ACR-QA | Bandit (standalone) | Semgrep (standalone) | CodeQL |
|-----------|--------|--------------------|--------------------|--------|
| Multi-tool aggregation | ✓ | ✗ | ✗ | ✗ |
| ECDSA-signed provenance | ✓ | ✗ | ✗ | ✗ |
| CI quality gate | ✓ | ✗ | Partial | ✓ |
| Inter-procedural taint | Shallow | ✗ | Partial | Deep |
| ORM-internal SQLi | ✗ | ✗ | ✗ | Partial |
| Memory safety (C/C++) | ✗ | ✗ | ✗ | ✓ |
| Precision (security-tier) | 24.7–37.9% | 14.0% | 36.0% | ~60–80% (est.) |

---

## Summary for Defence

**Q: What can't your tool find?**

Three categories of honest misses:

1. **ORM/framework-internal vulnerabilities** (2 documented: CVE-2024-36039,
   CVE-2024-42005) — the vulnerable code is inside library internals; the application
   call site contains no detectable pattern. This is an inherent limitation of
   pattern-based static analysis.

2. **Logic bugs** — business logic errors, authorisation bypasses, race conditions.
   These require semantic understanding beyond syntactic pattern matching.

3. **Novel vulnerability classes** without existing rule coverage. ACR-QA's rule base
   is a snapshot; new vulnerability classes require new rules.

These limitations are not bugs — they are the known scope boundaries of the
static analysis technique. ACR-QA's 100% recall on statically-detectable CVEs
confirms it fully covers the classes it is designed to detect.
