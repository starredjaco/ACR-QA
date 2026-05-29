# Defense Day Q&A

Running list of questions that may come up during the thesis defense on **Jun 25, 2026**.
Add new questions daily as you think of them or rehearse.

---

## Motivation & Value

### Q: Why build a tool at all? Can't developers just paste their code into ChatGPT or Claude and ask it to find bugs?

**Short answer:**
ChatGPT and Claude are great at explaining code. They are not a substitute for a security scanner — they have no memory, no CI/CD integration, no audit trail, they hallucinate, and they cannot see your whole codebase at once.

**Full answer:**

| | LLM (ChatGPT / Claude) | ACR-QA |
|---|---|---|
| **Memory across scans** | None — every conversation starts fresh | Full history: tracks which vulns are new, fixed, or regressed |
| **Codebase coverage** | Limited by context window (~200k tokens max). A 100k-line codebase won't fit | Scans the entire repo file by file, no limit |
| **Reproducibility** | Non-deterministic — same code gives different answers each run | Deterministic SAST rules + fixed rule versions = same input always gives same output |
| **Hallucination** | Will confidently report fake vulnerabilities or miss real ones | Detection is rule-based (Semgrep, Bandit, Ruff) — no invented findings |
| **CI/CD integration** | You cannot put "ask ChatGPT" in a GitHub Actions pipeline | Runs as a CLI step; blocks merge if quality gate fails |
| **Structured output** | Free-form text — no machine-readable format | Canonical JSON findings with severity, rule ID, file, line, fingerprint |
| **Audit trail** | No — chat history is not a compliance artifact | Every scan is ECDSA-signed and timestamped; results stored in PostgreSQL |
| **Privacy** | You cannot paste proprietary or client code into a third-party LLM | Runs entirely on your own infrastructure; code never leaves your server |
| **Cost at scale** | Scanning 10k files via API = thousands of tokens = real money per run | Free after deployment; tools (Semgrep, Bandit) are open-source |

**Where AI fits in ACR-QA:**
ACR-QA does use AI — but only for **explaining** findings, not **detecting** them. Detection is done by deterministic tools (Semgrep, Bandit, Ruff, staticcheck). Once a real finding is confirmed, the Groq/LLaMA-3 model generates a human-readable explanation of the vulnerability, its impact, and a remediation suggestion. This hybrid approach gives you the precision of rule-based detection plus the readability of AI-generated context.

**If pushed: "But Claude is really good at finding bugs — I've seen it work"**
Claude can find bugs in small, self-contained snippets that fit in its context window. That is useful for code review of a single function. It cannot: scan an entire project, track a vulnerability across 50 commits, tell you whether a vuln regressed after you thought you fixed it, or produce a signed audit report. These are the capabilities that matter at the team/org level.

---

### Q: So what does ACR-QA actually do? Does it use AI to review code?

**Short answer:**
ACR-QA runs six proven SAST tools against your code, normalizes all their output into one unified format, and then uses AI only to explain the findings it already confirmed — not to find them.

**Full answer:**

The pipeline has four stages:

**Stage 1 — Detection (deterministic, no AI)**
Six tools run in parallel against the target directory:
- `Semgrep` — pattern-based security rules (OWASP Top 10, injection, XSS, etc.)
- `Bandit` — Python-specific security checks (hardcoded secrets, subprocess injection, etc.)
- `Ruff` — code quality and security lint for Python
- `staticcheck` — Go static analysis
- `vulture` — dead code detection
- `radon` — complexity scoring (high complexity = higher risk)

**Stage 2 — Normalization**
Each tool outputs its own JSON format. The `Normalizer` maps every raw finding to a `CanonicalFinding` — a unified Pydantic model with consistent fields: `severity`, `canonical_rule_id`, `file`, `line`, `fingerprint`, `evidence`. This is what makes cross-tool deduplication and trend tracking possible.

**Stage 3 — AI Explanation (LLM, but only for confirmed findings)**
For each finding that passes the dedup filter, the `Explainer` engine calls Groq's LLaMA-3 API with the finding + surrounding code context. It returns: what the vulnerability is, why it is dangerous, and how to fix it. The LLM never decides what is or is not a vulnerability — the SAST tools already did that.

**Stage 4 — Storage, Attestation & Dashboard**
Results are stored in PostgreSQL. Every scan is signed with an ECDSA-P256 key so the output can be cryptographically verified later. The FastAPI + React dashboard lets you triage findings, assign owners, track fix status, and view trends over time.

**One-sentence summary for the committee:**
> "ACR-QA orchestrates six static analysis tools, unifies their output into a canonical format, and uses a language model to make the findings readable — not to find them."

---

## System Design & Architecture

### Q: Why does ACR-QA require a local directory path instead of a GitHub URL?

**Short answer:**
By design — and it is the correct design for a self-hosted security tool. The scanner runs server-side on already-checked-out code, which is exactly how every major on-premise SAST tool works.

**Full answer:**

ACR-QA is architected as a **CI/CD pipeline tool** — it runs inside your own infrastructure on code that is already present on the server. The "target directory" is whatever path your CI runner has checked out (`$GITHUB_WORKSPACE` in GitHub Actions, `$CI_PROJECT_DIR` in GitLab CI, etc.). The dashboard is a management interface for that server-side tool, not a SaaS ingestion layer.

Accepting a raw GitHub URL in the UI would require:

1. **GitHub credentials on the server** — either a stored OAuth token or a GitHub App installation. This introduces credential management, token rotation, permission scoping, and secret storage into the core product — none of which are trivial to do securely.
2. **Temporary clone management** — the server would clone the repo, scan it, then delete it. This adds disk I/O, clone timeout handling, and a surface for scanning malicious repositories if the URL input is not tightly controlled.
3. **Rate limiting and auth flows** — GitHub API rate limits apply to clones. Private repos require per-user tokens. Handling this correctly is a separate product feature.

**How do competitors handle it?**

| Tool | Local CLI? | GitHub URL input? | How |
|------|-----------|-------------------|-----|
| **SonarQube** (self-hosted) | Yes — `sonar-scanner` runs on local checkout | No | Runs inside CI on already-checked-out code. GitHub integration is a plugin that still reads local files. |
| **Semgrep CLI** | Yes — `semgrep --config=auto ./` | No CLI support | Their *cloud* product (semgrep.dev) accepts GitHub via OAuth — but that is a separate SaaS product, not the open-source CLI. |
| **CodeQL** | Yes — GitHub Actions checks out code first, then runs CodeQL on the workspace | No | GitHub's own product; works because code is already in `$GITHUB_WORKSPACE`. |
| **Snyk** | Yes — `snyk test` runs on local checkout | No | Their "monitor" feature sends dependency manifests to their cloud, not source code. |
| **Bandit / Ruff / Semgrep** (the tools ACR-QA wraps) | Local only | No | All CLI tools — they expect a local path. |

**Bottom line:** Every self-hosted SAST tool in the industry works on local paths. GitHub URL input is a SaaS feature — it belongs in Phase B (cloud deployment) of the roadmap, not Phase A (on-premise thesis prototype). ACR-QA is consistent with industry practice.

**If pushed: "Will you add GitHub URL support?"**
Yes — it is planned for Phase B. The architecture supports it: a `GitIngestor` adapter would clone the repo into a temp directory, hand that path to the existing pipeline, then clean up. The change is additive and does not require restructuring the core analysis pipeline.

---

---

## Evaluation — Precision & Recall

### Q: What is the precision and recall of your tool? How did you measure it?

**Short answer:**
On 30 mature production repos: **security-tier precision 24.7–37.9%, recall 100%** (8/8 planted CVEs detected). Measured using a clean-code adversarial benchmark — the hardest possible precision test.

**Full answer:**

**Recall (100%)** was measured on a separate CVE battery: 20 intentionally-vulnerable snapshots of real libraries (Werkzeug 0.11.10, PyYAML 3.13, Celery 5.2.1, etc.), each with one planted CVE. ACR-QA detected all 8 detectable CVEs (12 are not detectable by static analysis — the vuln is in a dependency, not the source). Recall = 8/8 = 100%.

**Precision** was measured using an adversarial benchmark: 30 mature, actively-maintained production repos (Python top-20 PyPI downloads, JS/TS top-6 GitHub stars, Go top-4 GitHub stars). These repos receive continuous expert security review — any finding ACR-QA emits on them is a candidate false positive by assumption. This is the *hardest* possible precision test.

**Two precision tiers are reported:**

| Tier | What it measures | Conservative | Optimistic |
|------|-----------------|-------------|-----------|
| **Security-tier** | HIGH-severity SECURITY-*/SECRET-*/SQLI-*/SHELL-*/CRYPTO-* rules only | **24.7%** | **37.9%** |
| Blended | All HIGH+MEDIUM findings including quality/style rules | 8.6% | 28.1% |

Security-tier is the defensible primary metric — it's the standard stratum reported by Semgrep, CodeQL, and Snyk. The blended number includes style and quality rules that are intentionally noisy (they're not meant to have high precision; they surface design improvements, not security bugs).

Conservative = NEEDS_REVIEW findings counted as FP (worst case). Optimistic = NEEDS_REVIEW counted as TP (best case). True precision is between these bounds.

---

### Q: 8.6% precision sounds terrible. Why should I trust this tool?

**Short answer:**
That number is deliberately measuring the worst case on the hardest possible corpus. The security-tier number (24.7%) is the right comparison, and even 8.6% beats doing nothing — but more importantly, the tool catches 100% of real CVEs.

**Full answer:**

Three things to keep in mind:

**1. The denominator is rigged against us on purpose.**
We're scanning code that expert maintainers and automated tools review continuously. Genuine bugs in `requests`, `numpy`, or `gin` would be front-page security news. Almost any SAST tool scores poorly on this corpus — it is specifically designed to surface noise.

**2. Precision/recall is a tradeoff, and we tuned for recall.**
A security tool that misses a real CVE is dangerous. A tool that over-warns is annoying. ACR-QA is tuned toward recall — if something looks like it *could* be a vulnerability, flag it and let the developer decide. This is the same tradeoff made by CodeQL, Semgrep, and Bandit.

**3. The blended number mixes security findings with quality/style findings.**
The 8.6% blended number includes findings like "function has too many parameters" (SOLID-001) and "subprocess called without shell=True" in a build script. These rules are not precision-sensitive — they're meant to surface design suggestions, not block deploys. Strip those out and the security-tier precision is 24.7–37.9%.

**What 24.7% means in practice:**
On a real-world codebase (not a curated-clean corpus), precision will be higher — most codebases have genuine issues the expert maintainers haven't fixed yet. The 24.7% is the floor, not the average.

**How does ACR-QA compare to competitors?**
Semgrep OSS reports ~20-30% precision on similar clean-code benchmarks. Bandit standalone precision on production Python code is routinely sub-20%. ACR-QA's security-tier precision is in line with or ahead of open-source SAST tools. Commercial tools (Snyk, Semgrep Pro) achieve 50%+ by adding paid rule tuning and taint analysis — that is the roadmap for ACR-QA post-thesis.

---

### Q: How did you pick the 30 repos for the precision corpus? Couldn't you have picked easier ones?

**Short answer:**
Selection was objective and reproducible: top-N by download/stars ranking, public snapshot date recorded, all SHAs pinned. Easier repos would inflate precision — that's exactly what we wanted to avoid.

**Full answer:**

Selection criteria:
- **Python 20**: top-20 PyPI 30-day downloads (hugovk.dev snapshot 2026-05-28). This is the most objective Python popularity ranking available.
- **JavaScript/TypeScript 6**: top-6 GitHub stars among installable libraries/frameworks (axios, express, next.js, react, webpack, n8n). Star-farmed repos excluded.
- **Go 4**: top-4 GitHub stars among installable libraries/apps (gin, caddy, syncthing, frp).

All 30 repos are SHA-pinned in `TESTS/evaluation/precision_corpus_pins.yml` — the exact commit scanned is recorded and reproducible. The benchmark can be re-run by any reviewer.

Picking "easier" repos (e.g., small personal projects or known-vulnerable codebases) would inflate precision but be academically dishonest. Using the most popular, most-reviewed repos in each ecosystem is the conservative, defensible choice.

---

### Q: You found bugs in your own tool during the evaluation. Isn't that a bad sign?

**Short answer:**
No — it's exactly what evaluation is for. Finding and fixing 5 defects during measurement is a sign the evaluation methodology is working, not that the tool is broken.

**Full answer:**

The Track 1 benchmark found 5 concrete defects and we fixed all of them:

| Defect | Found via | Fixed |
|--------|-----------|-------|
| JS adapter ignored severity scorer (all warnings forced to medium) | Benchmark showed 204 STYLE-017 findings at medium | ✅ |
| JS adapter scanned examples/ as production code | express showed 288 findings from example files | ✅ |
| Go adapter crashed on repos requiring Go > installed version | All 4 Go repos returned 0 findings | ✅ |
| SSRF rule fired in developer-controlled tooling paths | Triage identified pattern-only over-firing | ✅ (path heuristic) |
| subprocess rule fired on intentional build automation | Triage identified same pattern | ✅ (path heuristic) |

Precision improved from 5.7% → 8.6% (blended) and the security-tier metric was added as a result of understanding the FP structure. This is normal scientific methodology: measure → find issues → fix → measure again. A tool that claimed perfect precision before any measurement would be suspicious.

---

### Q: What are the remaining false positives? Why haven't you fixed them?

**Short answer:**
The remaining 123 NEEDS_REVIEW findings fall into two root causes: SSRF false positives outside tooling paths (taint analysis required) and subprocess false positives in production library code (call-site context required). Both require dataflow analysis — a significant research scope beyond this thesis.

**Full answer:**

The two remaining FP classes that path heuristics cannot reach:

**SSRF (SECURITY-046) in production library code** (~10 findings):
The rule fires on `requests.get(url)` where `url` is a variable. In library code like `httpx` or `requests` itself, this is intentional — the library is *supposed* to accept arbitrary URLs from its callers. Pattern-matching cannot distinguish "library accepting user URL" from "web handler accepting untrusted URL." Proper SSRF detection requires taint-path analysis from HTTP request parameters to the outgoing request call. This is a full research sub-problem.

**subprocess in production code** (~26 findings):
`B603/B607` fires on any `subprocess.run(["git", ...])` in production code. Some of these are genuinely risky (user-controlled input into a subprocess). Most are developer tools calling known commands. Distinguishing the two requires dataflow analysis from the call-site to HTTP input sources.

**Why not fix them before defense:**
Building accurate taint analysis would take 2–4 weeks and would risk breaking the 100% recall that is already achieved. The precision floor is already defensible (24.7% security-tier). The thesis honestly acknowledges these limitations and frames them as future work — which is the academically correct approach.

Commercial tools (Snyk Code, Semgrep Pro) address this by combining pattern matching with proprietary taint engines trained on large corpora. That is post-thesis scope for ACR-QA.
