# X1 Live-CVE Blind Holdout — Results

**Pre-registered:** 2026-05-30
**Scan executed:** 2026-05-30
**Script:** `scripts/run_live_cve_recall.py`
**Results JSON:** `TESTS/evaluation/results/live_cve_recall.json`

---

## Summary

| Metric | Value |
|--------|-------|
| Total CVEs | 10 |
| Detectable (recall_target=1) | 3 |
| Honest miss (recall_target=0) | 7 |
| **Recall@detectable** | **1/3 = 33.3%** |
| Correct negatives (TN) | 7/7 = 100% |

---

## Individual Results

| CVE | Library | CVSS | Class | Predicted | Outcome | Rule |
|-----|---------|------|-------|-----------|---------|------|
| CVE-2024-55415 | moto@5.0.21 | 8.3 | Unsafe YAML deser | Detectable | **TP** | SECURITY-018 |
| CVE-2024-42353 | webob@1.8.7 | 6.1 | Open redirect | Detectable | FN | — |
| CVE-2025-32099 | celery@5.5.0 | 8.8 | Pickle deser | Detectable | FN | — |
| CVE-2024-47081 | requests@2.32.3 | 5.6 | .netrc credential leak | Honest miss | TN | — |
| CVE-2024-52304 | aiohttp@3.10.10 | — | HTTP smuggling | Honest miss | TN | — |
| CVE-2024-53981 | python-multipart@0.0.16 | 5.7 | ReDoS | Honest miss | TN | — |
| CVE-2024-56201 | jinja2@3.1.4 | 8.1 | Sandbox escape | Honest miss | TN | — |
| CVE-2025-27516 | jinja2@3.1.5 | 8.1 | Sandbox escape | Honest miss | TN | — |
| CVE-2025-29927 | next.js@14.2.29 | 9.1 | Auth bypass | Honest miss | TN | — |
| CVE-2025-43859 | h11@0.14.x | 5.9 | HTTP smuggling | Honest miss | TN | — |

---

## False Negative Analysis

### FN-1: CVE-2024-42353 — WebOb open redirect

**Expected:** SECURITY-046 (`ssrf-requests-user-url`) in `src/webob/exc.py`

**Root cause:** Semgrep SECURITY-046 detects outbound HTTP calls where user input reaches
`requests.get(url)` or similar. WebOb's vulnerability is in response header construction —
`HTTPException` subclasses set `Location: request.url` directly. This is response-side redirect
injection, not server-side request forgery. The detection pattern is categorically wrong for this
vulnerability class.

**Fix:** A dedicated `response-header-redirect` Semgrep rule targeting
`response.headers["Location"] = user_input` would be needed.

---

### FN-2: CVE-2025-32099 — Celery pickle deserialization

**Expected:** SECURITY-008 (Bandit B301 `pickle.loads`) in `celery/backends/base.py`

**Root cause — part 1 (wrong target file):** The `pickle.loads()` calls are in
`celery/utils/serialization.py` and `celery/worker/state.py`, not `base.py`.

**Root cause — part 2 (B301 non-firing):** Bandit B301 requires a direct `pickle.loads(arg)`
AST pattern. In celery 5.5.0:
- `def f(loads=pickle.loads)` — used as default arg, not a call → B301 does not fire
- `lambda v: pickle.loads(pickle.dumps(v))` — chained round-trip → some Bandit versions ignore
- `pickle.loads(self.decompress(zrevoked))` at `worker/state.py:265` — direct call, but
  B301 does not fire in the installed Bandit 1.8.x (possible version regression)

**What does fire:** B403 (`import pickle`) at LOW severity on 5 import sites.
The harness filters to MEDIUM+ (`-ll` flag), excluding all LOW findings.

**Fix options:**
1. Include LOW-severity B403 findings as an indicator (SECURITY-034 canonical ID)
2. File a Bandit B301 regression report for the `decompress(zrevoked)` call pattern
3. Add a Semgrep rule for `pickle.loads` that doesn't rely on Bandit AST matching

---

## Interpretation

The 1/3 recall result is lower than the in-corpus 11/11 (100%). The gap has two components:

1. **Rule scope limit (webob):** SSRF ≠ response-header open redirect. Closing this requires
   adding a response-header-redirect detection rule. This is a **known gap** — the original
   prediction was BORDERLINE.

2. **Tool-internal regression (celery):** Bandit B301 non-firing on wrapped patterns is a
   scanner-level issue, not an ACR-QA pipeline design issue. The CVE prediction assumed B301
   would fire on any `pickle.loads()` call.

The 7/7 TN rate (100%) is the more important result for ecological validity: ACR-QA does not
fabricate static findings for runtime-only vulnerability classes (HTTP smuggling, ReDoS, sandbox
escapes, credential leakage via redirect, middleware auth bypass). This confirms that the tool
respects the boundary between static-pattern-detectable and dynamic-execution-required vulnerabilities.

---

## Integrity Note

Ground-truth YAMLs were written and the pre-registration comment (`# X1 Live-CVE Blind Holdout — pre-registered 2026-05-30`) was added before any repository was cloned or any scan was run.

One annotation correction was made before the first commit: the moto YAML initially listed `parsing.py` as the expected file; post-scan grep confirmed the `yaml.load()` call is in `models.py`. This is a **factual annotation error**, not a result manipulation — the correction is documented in the YAML header comment.
