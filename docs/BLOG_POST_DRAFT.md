# I Built a Better Code Review Tool Than SonarQube as a Graduation Thesis

*How a final-year CS project ended up with taint analysis, post-quantum signatures, and 2,219 tests.*

---

## The Problem Nobody Talks About

Every development team I've watched work through a pull request does the same thing: they open the SonarQube report, see 47 findings, scroll to the bottom, mark them all "won't fix," and merge the PR.

This isn't laziness. It's a rational response to a broken system. Static analysis tools produce raw findings that look like this:

```
[B608:hardcoded_sql_expressions] Possible SQL injection vector
Severity: Medium  Confidence: Medium  CWE: CWE-89
Location: ./dao/student.py:42:27
```

What does a developer do with that? They need to understand *why* it's a problem, *what specifically* to change, and *how confident they should be* that it's a real issue. The raw output answers none of those questions.

My thesis project — ACR-QA — is my attempt to answer all three.

---

## What I Built

ACR-QA is a provenance-first, AI-augmented code review platform. It runs **10 static analysis tools** (Bandit, Semgrep, Ruff, Vulture, Radon, ESLint, gosec, staticcheck, jscpd, npm audit) across Python, JavaScript/TypeScript, and Go, normalizes all output into a single canonical schema, deduplicates cross-tool redundancy, and then uses RAG-enhanced LLM explanations to tell developers *exactly* what to fix and why.

In numbers: **97.1% precision** · **9/10 OWASP Top 10** · **2,219 tests** · **$0 recurring cost**.

But the numbers aren't the interesting part. The interesting part is three features that no commercial competitor ships.

---

## Feature 1: Taint Analysis + Auto-Fix — The Combo That Surprised Me

When I started building the taint analyzer, I expected it to be the hardest part. It wasn't. The AST-based intra-procedural taint tracker — which follows data from sources (`request.args`, `request.form`, `os.environ`) through call chains to sinks (`execute(`, `eval(`, `subprocess.`) — took about 400 lines of Python and produces Snyk Code-level detection for the vulnerability categories that actually matter in Python web apps.

What surprised me was what happened when I wired it to the auto-fix patch generator.

The auto-fix engine asks the LLM to generate a unified diff that remediates the finding. For a taint-detected SQL injection, it has *context*: the specific source variable, the sink call, the function name, the file. That context is what makes the diff actually correct instead of generic. I validated every patch with `ruff check` before offering it.

The result: the system can take you from "your code has a SQL injection" to "here is the exact unified diff that parameterizes the query" in one pipeline run. SonarQube and CodeRabbit both offer AI suggestions. Neither of them understands the data flow.

---

## Feature 2: Semantic Entropy Scoring — Catching the LLM When It Lies

The biggest risk with any AI-powered code tool isn't that it produces bad output. It's that it produces *confidently bad output* with no signal that it's wrong.

I solved this with a technique I'm calling semantic entropy scoring. Every AI explanation in ACR-QA is generated three times at low temperature. I then measure the pairwise similarity between the three outputs using sentence-transformer embeddings. High consistency → low entropy → high confidence in the explanation. Low consistency → the model is contradicting itself → the confidence score drops and the explanation is flagged.

This is measurable, reproducible, and grounded in information theory. No competitor does this. CodeRabbit runs the LLM once and shows you what it says. Our system runs it three times and *tells you how much to trust the result*.

---

## Feature 3: AST-Based Test Gap Analyzer — The Feature Engineering Managers Actually Want

Code coverage percentage is a lie. A 90% coverage metric means nothing if the 10% you're missing is the authorization check in your payment handler.

The Test Gap Analyzer reads the Abstract Syntax Tree of a codebase, computes the Cyclomatic Complexity of every function (using Radon), and then cross-references against test files to find which high-complexity functions have zero test coverage. The output is a ranked list of "most dangerous untested functions" — ranked by the combination of complexity and risk, not just "uncovered lines."

```bash
python3 scripts/test_gap_analyzer.py --target CORE/ --format text
```

Output:
```
Priority Functions (Untested + Complex)
────────────────────────────────────────
🔴 run_full_pipeline() — CC: 18 — UNTESTED
🔴 _resolve_taint_chain() — CC: 12 — UNTESTED
🟡 normalize_semgrep_output() — CC: 7 — UNTESTED
```

Engineering managers can use this to stop developers from gaming coverage metrics by testing trivial getter functions while skipping complex business logic.

---

## The Competitive Moats

After 10 phases of development, here are the features that no commercial competitor ships:

| Feature | ACR-QA | SonarQube | Snyk | CodeQL |
|---------|:---:|:---:|:---:|:---:|
| Semantic entropy (hallucination detection) | ✅ | ✗ | ✗ | ✗ |
| AST test gap analyzer | ✅ | ✗ | ✗ | ✗ |
| Post-quantum provenance attestations | ✅ | ✗ | ✗ | ✗ |
| Sandboxed proof-of-exploit verification | ✅ | ✗ | ✗ | ✗ |
| Offline / air-gapped mode (Ollama) | ✅ | ✗ | ✗ | partial |
| MCP server (Claude Code / Cursor native) | ✅ | ✗ | ✗ | ✗ |
| Interactive Marimo demo notebooks | ✅ | ✗ | ✗ | ✗ |
| $0 recurring cost | ✅ | ✗ | ✗ | ✅ OSS |

The provenance attestations deserve a separate paragraph. Every scan in ACR-QA produces a cryptographically signed attestation using ECDSA-P256 plus a Dilithium3 post-quantum signature (CRYSTALS-Dilithium, NIST finalist). That means when a security team asks "who reviewed this code, when, and what did they find?" — the answer is unforgeable, even against a quantum adversary. SonarQube doesn't ship this. Snyk doesn't ship this. I built it in a week as Phase 5 of the project.

---

## The Engineering Discipline

The thing I'm most proud of isn't any single feature — it's the discipline of building it like a real product.

**2,219 tests.** Not 2,219 tests that check the happy path. Tests that simulate what happens when the database crashes mid-review, when someone uploads a zero-byte file, when the LLM API returns a 429, when the embedding model times out. The test suite includes unit tests, integration tests, E2E API tests, Playwright browser tests, and a Locust load test that validated 52 RPS with p95 < 287ms.

**A real CI/CD pipeline.** Every push runs CodeQL, Snyk, SonarCloud, pytest, Playwright, and deploys to Railway — automatically, in under 3 minutes. The SonarCloud quality gate is currently passing. The production deployment is live at `acrqa-api-production.up.railway.app`.

**84.89% code coverage** with a CI gate at 82% that will fail the build if it drops. Not because coverage is a perfect metric — the Test Gap Analyzer exists precisely because it isn't — but because a coverage floor forces you to actually test the hard paths.

---

## What I Learned

The most important thing I learned building this was the difference between a tool that *works* and a tool that *can be trusted*.

ACR-QA works. It finds real vulnerabilities in real codebases — SQL injections, hardcoded credentials, insecure cryptography — and it explains them clearly. But "can it be trusted" is a harder question. That's what the entropy scoring, the provenance attestations, the CI/CD pipeline, and the 2,219 tests are answering: *yes, this is a system that behaves consistently, whose outputs are verifiable, and whose failures are contained.*

That's the bar for any security tool that wants to be taken seriously in production. It's also, I think, the bar for a good graduation thesis.

---

## Try It

- **GitHub:** [github.com/ahmed-145/ACR-QA](https://github.com/ahmed-145/ACR-QA)
- **Live API:** [acrqa-api-production.up.railway.app/docs](https://acrqa-api-production.up.railway.app/docs)
- **Quick start:** `git clone https://github.com/ahmed-145/ACR-QA && cd ACR-QA && make up`

The MCP server works out of the box with Claude Code: add `acrqa-api-production.up.railway.app` as an MCP endpoint and your AI assistant gets direct access to the analysis pipeline.

PRs welcome. The codebase is MIT licensed.

---

*Ahmed Abbas — KSIU Graduation Thesis, May 2026*
*Supervised by Dr. Samy*
