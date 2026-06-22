# RealVuln — Pure-Static Engine Results (2026-06-22)

> **Scored with the OFFICIAL RealVuln scorer** (`TESTS/evaluation/realvuln/score.py`),
> not the lenient inline scorer. Every unmatched finding counts as a false positive.
> All scanners scored on the **same 22 repos** (558 ground-truth true positives each).

## Headline: ACR-QA pure-static vs. commercial/OSS SAST

| Scanner | TP | FP | Recall | Precision | F2 |
|---------|----|----|--------|-----------|-----|
| **ACR-QA (acr-qa-hybrid-v1)** | **279** | 328 | **50.0%** | **46.0%** | **49.1%** |
| Semgrep | 98 | 224 | 17.6% | 30.4% | 19.2% |
| Snyk | 83 | 101 | 14.9% | 45.1% | 17.2% |
| SonarQube | 29 | 14 | 5.2% | 67.4% | 6.4% |

On this corpus ACR-QA shows ~2.8× the recall of the next-best tool (Semgrep) and ~2.5× the F2,
with precision higher than Semgrep and matching Snyk. SonarQube's higher precision (67.4%) comes
at a 5.2% recall — it finds almost nothing.

> ### ⚠️ This is in-sample coverage, not held-out generalization
> **The ACR-QA detectors in this run were developed against these 22 repos** — patterns were
> added by reading their ground truth (e.g. `autoescape=False` from dvpwa, `os.system`/`HttpResponse`
> from djangoat, the f-string-SQL relaxation to recover vfapi's CWE-89). Semgrep/Snyk/SonarQube
> were **not** tuned on this corpus. So this table measures **how completely ACR-QA's ruleset covers
> these specific CWE patterns vs. the competitors' default rules** — a real and defensible claim — but
> it is **not** evidence that ACR-QA reaches 50% recall on arbitrary unseen code. The detectors
> themselves (f-string SQL, ReDoS, `os.system`, SSRF) are legitimate general patterns any good SAST
> should catch, but the headline number is optimistic by an unknown margin.
>
> **The number a committee will believe** is a held-out one: freeze the engine and run it against
> repos *not* in these 22. That validation is still **TODO** (see `[[what_is_left]]`).

## What drives the result — a zero-LLM, zero-API deterministic engine

The recall comes entirely from `scripts/ast_security_scanner.py`, a pure Python `ast`-based
analyzer (plus a regex fallback for Python-2 source that fails to parse). No model calls, no
network, fully reproducible. It is complemented by targeted Semgrep boost rules. **Bandit is
disabled by default** (`ACRQA_RV_BANDIT=1` to re-enable for ablation): it contributed 330 FPs
for ~26 unique TPs (22.5% precision), dragging the pipeline down.

### Detector coverage (CWE)
Injection (79/89/78/918/22/1336/94/601/502), auth/access (306/307/352/384/287/522/256/862/284),
config/crypto (798/259/215/16/295/338/916/328/327/614/1004/209/200), and resource (400/1333 ReDoS).

### Key engine techniques added this session
- **ReDoS (CWE-400/1333):** stack-based catastrophic-backtracking regex detector (e.g. `((a)+)+`).
- **Extended SSRF (CWE-918):** `urllib`/`http.client`/single-param wrapper taint, not just `requests.*`.
- **SSTI (CWE-1336):** `Jinja2.from_string(dynamic)` in addition to `render_template_string`.
- **autoescape=False:** cross-file detection → flags unescaped template vars repo-wide.
- **f-string SQL (CWE-89):** any interpolated value in SQL string (catches FastAPI route params
  that taint heuristics miss — mirrors Bandit B608 at higher precision).
- **`os.system` dynamic arg (CWE-78)** and **Django `HttpResponse`/`HttpResponseRedirect`** XSS/redirect.

### Precision discipline
- **Official-scorer alignment:** the inline scorer in `run_realvuln_hybrid.py` was rewritten to
  count every unmatched finding as FP (it previously only counted GT-trap hits, inflating
  precision from a true ~26% to a reported 91%). Spot-checked identical to `score.py` on vfapi;
  a 3-finding aggregate gap remains (inline 276/331 vs official 279/328), so **the official
  `score.py` is the source of truth** and all headline numbers above are the official ones.
- **Noise-path exclusion:** test/fixture/migration files are skipped (0 GT TPs lost, ~80 FPs removed).
- **Sensitive-route gating (CWE-306):** missing-auth is flagged only on privileged/state-changing
  routes, not public ones (index/login/health) — cut 71 net FPs.
- **Dropped net-negative heuristics:** bare CWE-200 "dict has a password key"; per-form CWE-352 spray.

## Reproduce

```bash
# Run the pure-static benchmark (Bandit off by default)
.venv/bin/python scripts/run_realvuln_hybrid.py --all --static-only

# Verify with the official scorer
cd TESTS/evaluation/realvuln
../../../.venv/bin/python score.py --repo realvuln-vfapi --scanner acr-qa-hybrid-v1
```
