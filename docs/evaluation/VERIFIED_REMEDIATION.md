# ACR-QA Verified Remediation (Track C — v8 Plan, Pillar P1)

> **Created:** 2026-06-03
> **ACR-QA version:** 5.0.0rc1
> **Status:** Engine implemented, unit-tested, demo script ready

---

## The Frontier

The entire SAST+autofix industry retests fixes with a *static re-scan*:

| Tool | Fix retest method | Accuracy claim |
|---|---|---|
| Snyk Agent Fix | Static re-scan | 80% |
| Apiiro AI-SAST | Reachability + AI reasoning | — |
| Checkmarx Assist | Static re-analysis | — |
| **ACR-QA** | **Live exploit re-run (ground truth)** | **Binary: fires or doesn't** |

**ACR-QA is the only tool that re-runs the actual exploit after applying the fix.**
If the exploit fails → fix_verified=True. If it still fires → fix_verified=False. Ground truth,
not probability.

---

## The 5-Step Pipeline

```
1. verify_before()  — ExploitVerifier on ORIGINAL code
                       → must return "verified-exploitable"

2. generate_patch() — AutoFixEngine.generate_patch() (LLM-powered)
                       → patch applied to a temp sandbox copy

3. apply_patch()    — write patched code to tmpdir (original untouched)

4. verify_after()   — ExploitVerifier on PATCHED code
                       → same exact payload, same route
                       → must return "verified-unexploitable"

5. attest()         — ECDSA-sign (vuln_proof, fix_diff, fix_proof)
                       → single Rekor-logged bundle
                       → auditor can replay the chain
```

`fix_verified=True` if and only if steps 1 AND 4 both succeed.

---

## Vulnerability Classes Supported (end-to-end)

| Class | Rule | Fixture | Exploit | Patched to |
|---|---|---|---|---|
| SQL injection | SECURITY-027 | `flask_sqli` | `' OR 1=1--` | Parameterized query |
| Command injection | SECURITY-021 | `flask_cmdi` | `; echo EXPLOITED` | subprocess list, no shell |
| SSTI (Jinja2) | SECURITY-031 | `flask_ssti` | `{{7*7}}` → `49` | Markup.escape before render |

---

## The Signed Bundle (Verified Finding v2)

```json
{
  "schema": "verified_remediation_v2",
  "finding_id": "...",
  "canonical_rule_id": "SECURITY-027",
  "fix_verified": true,
  "vuln_proof": {
    "tier": "verified-exploitable",
    "payload": "1 UNION SELECT sqlite_version()--",
    "evidence": "[(1, 'admin', 'admin@example.com'), ...]",
    ...
  },
  "fix_diff": "--- a/app.py\n+++ b/app.py\n-query = f'SELECT...{user_id}'\n+query = ('SELECT...?', [user_id])",
  "fix_proof": {
    "tier": "verified-unexploitable",
    "payload": "1 UNION SELECT sqlite_version()--",
    "evidence": "no rows leaked",
    ...
  },
  "signature": "ECDSA-P256:...",
  "rekor_log_index": ...
}
```

An auditor sees: exploit working → patch applied → exploit failing → cryptographically chained.
Nobody else signs the fix.

---

## Test Coverage

- **15 unit tests** in `TESTS/test_verified_remediation.py` — all passing, no Docker required
  - `RemediationResult` serialisation and summary line
  - Diff generation (changed/identical)
  - Step 1 abort (exploit doesn't fire), Step 2 abort (no patch), Step 4 abort (exploit still fires)
  - Full success path (mocked exploit results)
  - Batch skips ineligible findings
  - Attestation called exactly once on verified result
  - JSON serialisability of full result
- **2 integration tests** (`@pytest.mark.exploit`) — require Docker, run `pytest -m exploit`

---

## Run the Defense Demo

```bash
# Requires: Docker daemon running + .venv active
python3 scripts/run_verified_remediation_demo.py
```

Output:
```
=================================================================
  ACR-QA Verified Remediation Demo
=================================================================

  The frontier: detect → exploit-fires → AI fix → re-run same exploit
  → confirm it now fails → sign (vuln_proof, fix_diff, fix_proof).
  Snyk retests with a static engine. We retest with the live exploit.

=================================================================
  Scenario: SQL Injection
=================================================================

  Running SQL Injection scenario...
  ✅ FIX VERIFIED — SECURITY-027 in app.py [12.3s]

  Patch applied:
  -    query = f"SELECT * FROM users WHERE id = {user_id}"
  +    query = "SELECT * FROM users WHERE id = ?"
  +    rows = conn.execute(query, [user_id]).fetchall()

  Attestation: ✅ signed
```

---

## Why This Matters for the Defense

- **The one sentence:** "We don't just generate a fix and static-rescan it. We re-run the exact
  exploit payload against the patched code and cryptographically sign the proof."
- **The competitor contrast:** Snyk claims 80% fix accuracy via static retest. ACR-QA's fix
  accuracy is measured by live exploitation — binary ground truth.
- **The auditor value:** A SOC2 auditor gets a tamper-evident chain: exploit-working + patch-diff
  + exploit-failing, all signed. Not "the scanner ran" — "the fix closes the exploit, provably."

---

## Engine Location

- `CORE/engines/verified_remediation.py` — `VerifiedRemediationEngine`, `RemediationResult`
- `scripts/run_verified_remediation_demo.py` — one-command defense demo
- `TESTS/test_verified_remediation.py` — 15 unit + 2 integration tests
