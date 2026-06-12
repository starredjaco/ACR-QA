# ACR-QA — Full Speaker Script (Slides 1–20)

15 minutes total. ~45 seconds per slide. **Bold = key phrases to land clearly.** Calm pace;
let the slide sit for 3 seconds before you speak — let the audience read the headline.

---

## Slide 1 — Title / Cover

> "Good morning. My name is Ahmed and my project is ACR-QA — an automated code-review and
> quality assurance platform for detecting real vulnerabilities in real code. Over the next
> 15 minutes I'm going to show you why most security scanners produce noise, what we built
> instead, and why it's ready to ship."

*(Pause. Click.)*

---

## Slide 2 — The Hook ("AI-written code, 1.88× more vulnerabilities")

> "Here's the problem. AI now generates a third of new code in enterprise teams. Researchers at
> Stanford found that code — even AI code — carries **1.88 times more security vulnerabilities**
> than code written by experienced developers alone. That's a 107% jump year-on-year in reported
> CVEs. Most teams respond by running a scanner — and that scanner returns hundreds of alerts,
> most of which are noise. So developers learn to ignore the scanner. Which one breaches you?
> Nobody knows."

*(Pause. Click.)*

---

## Slide 3 — Problem: The Noise Tax

> "This is the actual problem. It's not that scanners miss bugs — it's that they produce so
> many alerts that **the signal drowns in the noise**. A team I interviewed was ignoring their
> scanner after it hit a 70% false-positive rate. The cost isn't just wasted time; it's the one
> real vulnerability that got buried under 500 false ones. That's the noise tax — and every
> team pays it."

*(Click.)*

---

## Slide 4 — ACR-QA: The One-Line Answer

> "ACR-QA's answer is not 'a better scanner.' It's a **trust layer on top of detection**. We don't
> just flag a vulnerability — we verify it is real, grade its trustworthiness, and sign the result.
> The headline number is **96.4% precision** on the Confirmed Tier — meaning fewer than 4 in 100
> confirmed findings are false positives. That's high enough to **automatically block a merge**
> without a human review."

*(Click.)*

---

## Slide 5 — Market Reality (Stat Cards)

> "The market context: enterprise static analysis tools cost between ten and fifty thousand
> dollars per year. ACR-QA is **fully self-hosted, open-source, zero licence cost**. The
> regulatory wind is in our favour — the EU Cyber Resilience Act and SLSA supply-chain
> requirements are now mandatory; ACR-QA already produces **SLSA-grade signed attestations**.
> We're not building for the market that exists — we're building for the market that's arriving."

*(Click.)*

---

## Slide 6 — Core Innovations (What Makes It Different)

> "Three innovations, not features. First: the **Confirmed Tier** — a four-gate filter that
> elevates only findings that are high-severity, match a curated rule set, sit in production code
> paths, and are confirmed by Bandit at high confidence. Second: **exploit verification** — we
> actually fire a safe payload in a Docker sandbox and confirm the vulnerability detonates. Third:
> **cryptographic attestation** — every scan is signed with ECDSA-P256 plus a post-quantum
> Dilithium3 signature, so the result is tamper-evident and auditable."

*(Click.)*

---

## Slide 7 — Architecture (Pipeline Diagram)

> "The pipeline: a CLI or GitHub Action triggers the analysis. Six tools run **in parallel** —
> Ruff, Semgrep, Bandit, Vulture, Radon, JSCPD. Every tool output is normalised into a single
> schema — the CanonicalFinding — so no downstream engine sees raw tool noise. The taint
> analyser traces data flows; the quality gate enforces thresholds; the AI explanation engine
> grounds its output in a retrieval corpus. All results land in PostgreSQL, served by a FastAPI
> layer, displayed in a React dashboard with live scan progress over SSE."

*(Click.)*

---

## Slide 8 — The Confirmed Tier (Four Gates)

> "The Confirmed Tier in detail. Gate one: **severity HIGH** only. Gate two: rule must be in
> our **curated 22-rule set** — not every rule Semgrep knows, only the ones we've validated.
> Gate three: the file must be in a **production code path** — not tests, not fixtures, not
> vendored code. Gate four: **Bandit must agree** at HIGH confidence. All four gates must pass.
> On the payments-api demo scan: **1,942 raw tool outputs → 219 unique findings → 151 high-severity
> → 55 Confirmed Tier**. That's the funnel. The 55 are real."

*(Click.)*

---

## Slide 9 — Confirmed Tier Funnel (Visual)

> "This is that funnel visually. Each bar is a gate. You can see the dramatic narrowing —
> 1,942 down to 55. The green bar is what auto-blocks. The question a committee always asks
> is: 'do you miss real bugs by being this strict?' Yes — recall is 25.1% on our holdout
> corpus. We made a conscious trade: **high precision now, progressive recall later**. A
> finding you're confident in is worth more than ten you're guessing about."

*(Click.)*

---

## Slide 10 — Evaluation Results (Table)

> "The evaluation. Across three datasets — RealVuln, our curated holdout, and the X6 zero-FP
> package set — the numbers hold. Confirmed Tier precision: **96.4%**. CVE recall on RealVuln:
> **25.1%, beating Semgrep at 17.5%**. And on six mature open-source libraries — numpy, pandas,
> pydantic, requests, httpx, SQLAlchemy — the high-severity false-positive rate is **0.0%**.
> The scanner stays quiet on clean code."

*(Click.)*

---

## Slide 11 — Three Proofs (Trust / Detonation / Attestation)

> "We made three claims. Here's the evidence for each. Trust: 96.4% precision on an independent
> holdout — not our training set. Detonation: five Docker exploit tests, all passing — SQL
> injection confirmed exploitable, safe code confirmed un-exploitable, SQL injection confirmed
> closed after remediation. Attestation: every bundle carries an embedded public key; a fresh
> process can verify a signature it didn't create — cross-process verification tested and green."

*(Click.)*

---

## Slide 12 — RAG Explanation Engine

> "One thing that sets this apart from a lint tool: the AI explanation is **grounded**. When
> ACR-QA explains a finding, it retrieves the relevant section of its knowledge base — OWASP
> descriptions, CWE mappings, rule rationales — and cites them. It doesn't guess. A hallucinated
> explanation would be worse than no explanation; a grounded one is an educational asset the
> developer actually reads."

*(Click.)*

---

## Slide 13 — OWASP Compliance View

> "The compliance view maps every finding to an OWASP Top 10 category. Here you see the live
> OWASP heatmap for the payments-api run — A02 Cryptographic Failures, A03 Injection, A08
> Software Integrity, A09 Logging. The score is calculated from the categories that pass clean.
> This is the report a security audit team asks for. It comes out of the box, automatically,
> for every scan."

*(Click.)*

---

## Slide 14 — Live Dashboard Screenshot (Overview)

> "This is the actual running dashboard — not a mockup. The fleet shows real production open-source
> repos alongside our three demo apps. The Trust Layer banner at the top is live — precision,
> recall, F1, self-scan result. The Confirmed Tier tile fetches from the API in real time.
> Everything you see here is data from a real scan, stored in a real database, served by a real
> API."

*(Click.)*

---

## Slide 15 — Attestation Screenshot ("Signature Verified")

> "And here — the attestation tab. After every scan, the system generates a signed bundle: ECDSA
> primary signature plus a post-quantum Dilithium3 signature. The green badge says
> **'Signature Verified'**. You can take that JSON, run it through the verify script, and
> independently confirm this exact scan, with these exact counts, happened at this exact time.
> That's compliance-grade provenance — for free, self-hosted."

*(Click.)*

---

## Slide 16 — Competitive Matrix

> "How does this compare? Semgrep: strong recall, no exploit verification, no attestation, SaaS
> pricing. Snyk: excellent dependency scanning, weak SAST, enterprise pricing, no exploit verification.
> SonarQube: broad language support, high false-positive rate, on-prem licence cost.
> ACR-QA: the only tool in this comparison with **exploit verification, SLSA attestation, and a
> $0 licence cost**. The trust wedge is the moat."

*(Click.)*

---

## Slide 17 — Current Implementation Status

> "Where are we today? 3,063 tests passing — unit, integration, and exploit. CORE coverage at 88%.
> The pipeline runs end-to-end on Python, JavaScript, and Go repos. The API, dashboard, and CLI
> are all production-grade. Docker exploit suite: 5/5 passing. PyPI wheel built. The only thing
> between this and a public release is the PyPI upload and a CSAF/VEX advisory stream — both
> straightforward."

*(Click.)*

---

## Slide 18 — The Ask ("What ACR-QA Delivers")

> "What I'm leaving you with: **Trust** — a precision high enough to auto-block without human
> review. **Proof** — we don't claim a vulnerability, we detonate it. **Reach** — real recall
> on production CVEs, beating the industry baseline. **Price** — zero. Every one of those is
> a concrete, measurable claim. The thesis documents the methodology, the evaluation, and the
> system design. The code is running right now on this machine."

*(Click.)*

---

## Slide 19 — Future Work

> "Three directions. First, **progressive recall** — expanding the curated rule set as we validate
> more rules at high precision. Second, **supply-chain integration** — SLSA provenance for
> dependencies, not just source. Third, **CNA status** — ACR-QA is designed to issue CVE IDs for
> vulnerabilities it discovers through exploit-verification. That's a long-term moat no open-source
> scanner has."

*(Click.)*

---

## Slide 20 — Close / Thank You

> "To summarise: we separated detection from trust. We built a four-gate filter that produces
> 96.4% precision on confirmed findings. We added exploit-verification so we can prove — not claim
> — a vulnerability is real. And we sign every result so the output is auditable. ACR-QA is not
> a scanner. It's a **trust layer for software delivery pipelines**. Thank you — I'm happy to
> take questions, or show you the live dashboard."

*(Stand still. Smile. Wait for the first question.)*

---

## Q&A Rapid-Fire Answers

| Question | Answer (one sentence) |
|----------|----------------------|
| "Why only 25% recall?" | We optimised precision first — 96.4% precision means every finding you act on is real; recall grows as we validate more rules. |
| "Is this production-ready?" | Yes — 3,063 tests, Docker exploit suite green, API + dashboard running right now. |
| "How does it compare to GitHub Advanced Security?" | GH Advanced Security has no exploit-verification and no attestation; it's a signal feed, not a trust layer. |
| "What's the business model?" | Open-core: the self-hosted version is free; a SaaS tier with managed signing keys and a CVE advisory feed is the commercial layer. |
| "Did you deploy it anywhere?" | It scanned its own repo (self-scan, 0 confirmed findings) and a suite of famous open-source repos including FastAPI, React, and requests. |
| "What is Dilithium3?" | A post-quantum lattice-based signature scheme — NIST-standardised — so attestations remain verifiable after quantum computing breaks RSA/ECDSA. |
