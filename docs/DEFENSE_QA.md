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

<!-- Add more questions below as you think of them -->
