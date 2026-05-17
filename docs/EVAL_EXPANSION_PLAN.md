# Evaluation Corpus Expansion Plan

**Status:** Not started · **Trigger:** After UI Phase 3 + testing complete · **Target:** v4.6.0
**Companion to:** `UI_PHASE_3_PLAN.md`, `UI_TESTING_PLAN.md`

---

## Mission

Strengthen ACR-QA's thesis-defendable claims by closing **three concrete gaps** in the eval corpus: no Go vulnerable target, no TS-only target, no large monorepo. Add 4 carefully-chosen repos (not 20 random ones) with proper ground truth labels.

## Why "Quality Over Quantity"

Each new eval repo needs:
- Cloning + setup (15 min)
- Manual finding labeling (1–2h)
- Ground truth YAML at `TESTS/evaluation/ground_truth/<repo>.yml`
- Recall test entry in `TESTS/evaluation/test_recall.py`
- Update to `EVALUATION.md` corpus tables
- Re-run of full eval

That's ~2h per repo. **4 repos = 8h. 20 repos = 40h of grunt work nobody reads.**

Phase 12 retrospective rule applies: *"If you can't say it in the thesis QA session, don't build it."* A defendable claim like *"evaluated across 16 repos spanning 4 languages"* is stronger than *"evaluated across 32 repos"* — the supervisor doesn't tally; they ask which ones.

---

## Current Corpus (12 repos)

| Category | Repo | Language | Role |
|---|---|---|---|
| Vulnerable (Python) | DVPWA | Python | Flask SQLi/MD5/hardcoded creds |
| Vulnerable (Python) | Pygoat | Python | Django full OWASP Top 10 |
| Vulnerable (Python) | VulPy | Python | Various Python vulns |
| Vulnerable (Python) | DSVW | Python | Damn Small Vulnerable Web |
| Vulnerable (Python) | vulnerable-flask-app | Python | Minimal Flask vuln |
| Vulnerable (Python) | bandit-test-cases | Python | Bandit's own test fixtures |
| Real-world (Python) | Flask (68k★) | Python | FP rate test, idiomatic Python |
| Real-world (Python) | httpx | Python | FP rate test, async patterns |
| Vulnerable (JS) | DVNA | JavaScript | Damn Vulnerable Node App |
| Vulnerable (JS) | NodeGoat | JavaScript | OWASP NodeGoat |
| Vulnerable (JS) | JuiceShop | JavaScript | OWASP Juice Shop |
| Vulnerable (JS) | dvws-node | JavaScript | Damn Vulnerable Web Services |

## Identified Gaps

| Gap | Why It Matters |
|---|---|
| **No Go vulnerable target** | We ship a Go adapter (gosec + staticcheck + Semgrep Go) but evaluate it only on gosec's self-tests. Cannot defend Go precision without a real vuln app. |
| **No pure TypeScript target** | We test JS adapter on `.js` files. Pure TS-only codebases exercise different code paths (interface stripping, type-only imports, `tsc` integration). |
| **No large real-world Python** | Flask is 68k★ but only ~10k LOC. We claim "42,000 LOC/s" — needs a real test on a 50k+ LOC codebase. |

---

## The 4 Repos to Add

### 1. **govwa** — Go Vulnerable Web App

**URL:** https://github.com/0c34/govwa
**Language:** Go
**LOC:** ~3,000
**Why:** The only widely-cited Go vulnerable web app. Covers SQLi, CMDi, XSS, auth bypass, file upload — perfect for testing gosec + Semgrep Go rules.

**Expected findings:** ~25 (SQLi in user lookup, CMDi in ping handler, hardcoded JWT secret, weak crypto)
**Defendable claim:** *"Go adapter validated on govwa with X% precision and Y% recall."*

---

### 2. **Django** — Real-world Python (76k★)

**URL:** https://github.com/django/django
**Language:** Python
**LOC:** ~250,000
**Why:** Different FP profile from Flask. Heavy ORM usage, metaclass magic, lots of `__init__.py` files, Django-specific patterns Bandit/Semgrep don't always understand. Real test of our FP-suppression engines (reachability, learned suppression, triage agent).

**Expected outcome:** < 5% FP rate on HIGH-severity findings. If higher, that's a real bug to fix.
**Defendable claim:** *"FP rate < 5% on Django (76k★, ~250k LOC) — validated on real production-scale codebase."*

---

### 3. **damn-vulnerable-typescript-app** (or **NodeGoat-TS** if available)

**Candidates:**
- `vulnerablecode/vulnerable-typescript-server` (small, ~2k LOC)
- `OWASP/NodeGoat` w/ `--lang typescript` flag (already exists in corpus but tested as JS)

**Decision:** Use NodeGoat-TS variant if it exists; otherwise create a minimal `test_targets/dvta/` with 6–8 known vulns we author ourselves (SQLi, prototype pollution, JWT none alg, ReDoS, etc.) — adds ~1h but gives us full ground truth control.

**Defendable claim:** *"JS/TS adapter validated separately on pure TypeScript codebase."*

---

### 4. **FastAPI** — Large Modern Async Python (74k★)

**URL:** https://github.com/tiangolo/fastapi
**Language:** Python
**LOC:** ~50,000
**Why:** Scale + async test. Validates our 42,000 LOC/s claim on a real codebase, not synthetic. Heavy `async/await` usage stresses the taint analyzer's call-graph handling.

**Expected outcome:** Scan completes in < 1.5s. FP rate < 3% on HIGH findings.
**Defendable claim:** *"Scans FastAPI (74k★, ~50k LOC, async-heavy) in < 1.5 seconds with < 3% FP rate."*

---

## Ground Truth Format

Each repo gets a YAML at `TESTS/evaluation/ground_truth/<repo>.yml`:

```yaml
repo: govwa
url: https://github.com/0c34/govwa
commit_sha: <pin to specific commit for reproducibility>
language: go

expected_findings:
  - rule_id: SECURITY-027
    file: vulnerabilities/sqli/sqli.go
    line: 42
    severity: high
    notes: "Concatenated user input into SQL query"
  - rule_id: SECURITY-021
    file: vulnerabilities/cmdi/cmdi.go
    line: 28
    severity: high
    notes: "User input passed to exec.Command"

out_of_scope:
  - rule_id: SECURITY-???
    file: vulnerabilities/idor/idor.go
    reason: "IDOR requires runtime testing (DAST); static analysis cannot detect"

recall_target: 0.85   # we expect to catch ≥ 85% of expected_findings
fp_budget: 0.05       # max 5% FP rate on HIGH severity
```

## Effort Budget

| Repo | Clone+Setup | Ground Truth Labeling | Tests + Eval YAML | Total |
|---|---:|---:|---:|---:|
| govwa | 0.25h | 1.5h | 0.25h | **2h** |
| Django | 0.25h | 1.5h (sample FPs from output) | 0.25h | **2h** |
| TS app | 0.5h (may need to author) | 1h | 0.25h | **1.75h** |
| FastAPI | 0.25h | 1.5h | 0.25h | **2h** |

**Total: ~8 hours.** All work labeled and reproducible.

---

## Execution Steps

1. Clone all 4 repos into `test_targets/eval-repos/` (gitignored)
2. Run ACR-QA on each with `--no-ai --json > /tmp/<repo>.json`
3. Manually classify each finding as TP / FP / out-of-scope
4. Write ground truth YAML for each repo
5. Add 4 new test functions to `TESTS/evaluation/test_recall.py`
6. Re-run full eval suite: `pytest TESTS/evaluation/ -m slow -v`
7. Update `docs/evaluation/EVALUATION.md`:
   - Per-repo precision/recall table grows from 4 → 8
   - Extended corpus table grows from 10 → 14 repos
   - Per-tool eval (`PER_TOOL_EVALUATION.md`) gets gosec/staticcheck columns

## Success Criteria

- [ ] 4 new repos cloned, scanned, ground-truth-labeled
- [ ] 4 new YAMLs in `TESTS/evaluation/ground_truth/`
- [ ] 4 new slow tests added to `test_recall.py` (one per repo)
- [ ] `EVALUATION.md` updated with new tables
- [ ] All 4 repos meet their `recall_target` (≥ 85% on vulnerable, < 5% FP on real-world)
- [ ] Defendable claim: *"Evaluated across 16 repos spanning Python, JavaScript, TypeScript, and Go"*

## Updated Numbers After Completion

| Metric | Before | After |
|---|------:|------:|
| Eval corpus size | 12 | 16 (+4) |
| Languages with vuln eval | 2 (Py, JS) | 4 (Py, JS, TS, Go) |
| Real-world FP-test corpus | 2 (Flask, httpx) | 3 (+Django) |
| Defendable corpus claim | "10-repo extended eval" | "16-repo 4-language eval" |

---

## What's Explicitly NOT Added

- ❌ **Mutillidae** — Java, out of scope
- ❌ **WebGoat** — Java, out of scope
- ❌ **Linux kernel** — overkill, would take 10h+ to scan
- ❌ **10+ random GitHub vuln repos** — no signal without ground truth
- ❌ **Closed-source samples** — can't ground-truth without internal docs
- ❌ **Self-contained ML projects** — different threat model, separate research scope

## Risks

| Risk | Mitigation |
|---|---|
| Ground truth labeling subjective on edge cases | Document each judgment call in YAML `notes:` field |
| New repos surface real product bugs (e.g., govwa breaks gosec adapter) | Treat as Phase 12 retrospective principle: real bugs are wins |
| Django scan finds 1000+ findings → labeling overwhelming | Only label HIGH severity + sample 30 MEDIUM; mark rest as "not labeled" |
| Adding repos delays demo video (task 12.35) | This plan runs AFTER UI Phase 3 + testing; demo video is on the critical path BEFORE this |
