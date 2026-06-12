# ACR-QA — Defense Speaker Script (18 slides · photo-first)

**Maps 1:1 to `docs/ACR-QA_Defense.pptx`** (18 slides). Target: **12–14 min** talk + **5 min** demo.
~40 seconds per slide.

**How to read:**
- **SAY** = near-word-for-word. **Bold** = land these slowly.
- **SIDE** = plain-English explanation for non-technical judges + "source?" answer for skeptics.
- **SOURCE** = the exact file/URL to cite if challenged. Know these.

> **The golden rule:** first sentence always needs zero background. Lead plain-English, add depth.
> **The kill line:** *"Most tools cry wolf. Mine brings you the wolf — then proves the cage holds."*

---

## Slide 1 — Title

**SAY:** "Good morning. I'm Ahmed. My project is **ACR-QA** — an automated code-review platform
that doesn't just *find* security bugs, it *proves* which ones are real and signs the proof.
Fifteen minutes."

**SIDE:** Set the frame: "trust" not "scanner." Say "proves" — it's the whole thesis.

---

## Slide 2 — The Hook

**SAY:** "AI now writes about a third of new enterprise code. And **45% of AI-written code ships
with a known security flaw** — that's Veracode's 2025 study. Meanwhile, open-source vulnerabilities
per codebase **jumped 107% in one year** — Black Duck's 2026 report. Your scanner now flags
nineteen hundred issues per project. **Which one breaches you?** Nobody can review that — so teams
either ship blind, or pay fifty thousand a year and still don't trust the output."

**SIDE:**
- *45%* = "almost half of what AI generates has a hole." **SOURCE:** Veracode 2025 GenAI Code
  Security report. URL in presenter notes.
- *+107%* = "the pile of alerts doubled in one year." **SOURCE:** Black Duck OSSRA 2026,
  SC Media coverage. URL in presenter notes.
- If asked "source?" name both. Never say "1.88×" — that stat was removed because it's unsourceable.

---

## Slide 3 — The Problem

**SAY:** "Three reasons teams can't trust automated review. **Quality variance** — a human reviewer
is inconsistent; the SQL injection on line 47 slips through on the fiftieth PR of the day.
**Cost** — enterprise tools are ten to fifty thousand a year, unaffordable for most teams.
**Hallucination** — AI explainers invent confident, wrong advice; a developer gets burned once and
never trusts the tool again."

**SIDE:**
- *Hallucination* = "the AI makes things up and says them confidently." The smoke-alarm analogy:
  "after enough false alarms, you take out the battery — and miss the real fire."
- **SOURCE for $10–50k:** `docs/PRICING_POSITIONING.md` + Snyk/Semgrep/SonarQube public pricing.

---

## Slide 4 — The Market Reality (stat cards)

**SAY:** "The same story as numbers. Enterprise tools: **ten to fifty thousand a year.** Vulnerabilities
per codebase: **up 107%.** AI-written code shipping a flaw: **45%.** ACR-QA: **zero** — self-hosted,
no licence, your data never leaves."

**SIDE:**
- This is the sell: risk is *rising* while the fix is *expensive* — except mine is $0.
- *Self-hosted* means *no subscription* and *no data leaving your network* — two enterprise concerns
  in one word.

---

## Slide 5 — The Solution: ACR-QA

**SAY:** "ACR-QA is a trust layer on top of your existing scanners. At merge time it answers one
question: *is this finding real enough to block automatically?* Four innovations make that work.
**RAG-grounded AI** — the explanation cites the actual rule, can't hallucinate. **Confirmed Tier**
— a strict four-gate filter at 96.4% precision. **Exploit verification** — detonates a real attack
in an isolated sandbox. **ECDSA + post-quantum signatures** — every scan is tamper-proof. All
on-premises, zero cost."

**SIDE:**
- *RAG* = open-book exam: it can't invent an answer because I hand it the rule text first.
- *96.4% precision* = "96 of 100 it flags are real bugs." **SOURCE:** `docs/evaluation/CONFIRMED_TIER.md`.
- *Exploit verification* = the locksmith analogy: *we pick the lock to prove it opens.*
- *Post-quantum* = future-proof against quantum computers. Say the word; don't explain lattices.

---

## Slide 6 — PR Operating Points (FIGURE: PR_OPERATING_POINTS.png)

**SAY:** "Before the demo numbers — this is the most important slide for understanding them. There
are **two operating modes on the same scan**. The gold diamond in the top-right corner: the
**Confirmed Tier** — 96.4% precision, safe to auto-block, lower recall. The navy circle to the
right: **Full Output** — 91% recall, trades precision for coverage, used for triage. **Both are
real. They are two points on one curve.** You pick the strictness for the job. Every 'which number
is real?' question has this diagram as the answer."

**SIDE:**
- *Top-right = ideal zone* (high precision AND high recall). Confirmed Tier is close; no tool is
  in the ideal zone — show the chart visually.
- This slide pre-empts T1 in QA_PREP ("are you cherry-picking?"). Say it before they ask.
- **SOURCE:** `ACR-QA-Book/figures/PR_OPERATING_POINTS.png` · `docs/evaluation/ABLATION_STUDY.md`.

---

## Slide 7 — Architecture (FIGURE: arch_overview.png)

**SAY:** "The system end-to-end. A developer pushes code — the webhook triggers a Celery worker.
**Twelve tools run in parallel**: Ruff, Semgrep, Bandit, and the rest. Every tool's output is
converted into one common format — the CanonicalFinding — so nothing downstream sees raw tool noise.
Then the trust gates: confidence scoring, reachability, taint, and the Confirmed Tier. The AI
retrieves the rule and explains it. Everything is stored, signed, and posted back. **Fourteen to
ninety seconds, end to end.**"

**SIDE:**
- *"One common format"* = different tools speak different languages; I translate them into one
  schema so I can reason about them together. A technical judge will ask about this — it's the
  `CanonicalFinding` Pydantic model in `CORE/engines/normalizer.py`.
- *"In parallel"* = fast AND independent — no tool's noise pollutes another's.
- **SOURCE:** `ACR-QA-Book/figures/arch_overview.png` — live generated from `arch_overview.puml`.

---

## Slide 8 — Live Dashboard: Fleet Overview (screenshot)

**SAY:** "This is the real running dashboard — not a mockup. It's already scanned a fleet of
projects including open-source libraries you'll recognise: **requests, httpx, FastAPI, Flask.**
The Trust Layer banner shows live KPIs. The Confirmed Tier tile fetches from the API in real time —
it was never estimated or hardcoded. You'll see it live in a few minutes."

**SIDE:**
- Stress "real, not a mockup" — committees assume student demos are faked. Famous repo names are
  your credibility: "I ran it on code the whole industry uses."
- If asked "is it live?" → "yes — API is running on localhost:8000 right now."

---

## Slide 9 — The Precision Funnel (FIGURE: FUNNEL_SLIDE.png)  ⭐

**SAY:** "This is the core result. On our **twenty-four-repository adversarial corpus**, the tools
produced **1,942 raw findings** — at that level only 8.6% are real. We filter by severity, then by
a curated security rule set, then by reachability and taint — and we land on **55 findings in the
Confirmed Tier, at 96.4% precision**, with **100% CVE recall preserved at every step.** Note the
right column — green all the way down. **We throw away the noise without throwing away the real bugs.**"

**⚠️ PRE-EMPT the trap — say this out loud:**
> "These numbers — 1,942 and 55 — are the *evaluation corpus*, twenty-four repos combined. The
> live scan you're about to see is *one* smaller app, so its confirmed count will be proportionally
> smaller. Same filter, smaller input."

**SIDE:**
- *96.4% precision* vs *100% recall* = two different questions: "am I right when I flag?" vs
  "did I catch them all?" Not contradictory — both measured, both real.
- **SOURCE:** `ACR-QA-Book/figures/FUNNEL_SLIDE.png` · `docs/evaluation/ABLATION_STUDY.md`.

---

## Slide 10 — Head-to-Head Benchmark (FIGURE: HEAD_TO_HEAD.png)

**SAY:** "The comparison on the same thirty-repo corpus. ACR-QA Confirmed Tier: **96% precision,
100% CVE recall, F₁ = 98.2%**. Semgrep CE: 46% F₁. Bandit: 22% F₁. The margin is **52 percentage
points** over the next best tool on F₁ — the combined measure of being both accurate and thorough."

**SIDE:**
- *F₁* = "a score that penalises you for being precise-but-missing things AND for flagging everything-but-wrong."
  Higher is better. **SOURCE:** `ACR-QA-Book/figures/HEAD_TO_HEAD.png` · `docs/evaluation/HEAD_TO_HEAD_BENCHMARK.md`.
- If asked "did you run Semgrep fairly?" → "yes, community rulesets p/default + p/python +
  p/javascript + p/go — the same set any user would apply. Methodology in `HEAD_TO_HEAD_BENCHMARK.md`."

---

## Slide 11 — RealVuln Leaderboard (FIGURE: REALVULN_LEADERBOARD.png)

**SAY:** "That was our controlled corpus. Here's the **real world** — the 2026 RealVuln benchmark:
22 actual production Python applications with known CVEs, independent third-party ground truth, a
published arXiv paper I didn't author. Strict matching: correct CWE category, correct file, correct
line within 10. ACR-QA: **25.1%** — leading Bandit, Semgrep, Snyk, and SonarQube. And I'll tell
you why it's not higher: a third of real-world vulnerabilities — auth logic, CSRF, IDOR — **cannot
be detected by any static tool.** That's Rice's theorem. I report the full-corpus number because
hiding it would be dishonest."

**SIDE:**
- *"Third-party ground truth I didn't author"* = I can't have cherry-picked these results.
- *25% sounds low* — own it and flip it: "Semgrep gets 17.5% on the same benchmark. SonarQube
  gets 6.5%. I'm leading the field on the hardest real-world test available."
- **SOURCE:** `ACR-QA-Book/figures/REALVULN_LEADERBOARD.png` · arXiv:2604.13764.

---

## Slide 12 — Exploit Verification (FIGURE: verified_remediation.png)

**SAY:** "This is what makes ACR-QA different from every tool in that chart. **We don't claim a
vulnerability — we detonate it.** Four phases. Phase 1: the rule maps to an exploit category —
SQL injection, command injection, template injection. Phase 2: a Docker container spins up, a real
payload fires — `' OR 1=1`, `;echo PWNED`, `{{7×7}}` — and we confirm the attack succeeded.
Phase 3: the AI generates a patch, the **same exact payload is fired again**, and we confirm it
*fails*. Phase 4: the whole chain — vulnerability proof, fix diff, re-exploit proof — is signed as
one ECDSA bundle. **Every result is a signed chain of evidence, not an opinion.**"

**SIDE:**
- *"Same payload fires again and must fail"* = this is what Snyk can't do. They retest statically.
  We retest with the live exploit — binary ground truth.
- *Docker container* = "an isolated throwaway computer — memory-capped at 128MB, destroyed after
  30 seconds, never touches any real system."
- **SOURCE:** `ACR-QA-Book/figures/verified_remediation.png` · `CORE/engines/exploit_verifier.py`.

---

## Slide 13 — Live Demo (section divider)

**SAY:** "Let me show you instead of telling you."

*(Switch to dashboard/terminal. Follow `docs/DEFENSE_DEMO_SCRIPT.md`. Three recovery lines if
anything breaks — it's in the script. The pre-seeded runs are your safety net.)*

---

## Slide 14 — Run Detail: payments-api (screenshot)

**SAY:** "One real scan — payments-api, a deliberately-vulnerable backend. **64 findings, 13
high-severity, 4 in the Confirmed Tier** — SQL injection, unsafe eval, hardcoded secrets. Each
finding shows its canonical rule ID, severity, confidence score. Tabs: compliance breakdown,
attestation, PR risk score."

**SIDE:**
- *4 confirmed* vs *55 in the funnel* — you pre-empted this on slide 9. If asked: "55 was across
  twenty-four repos; this is one app. Same filter, smaller input."

---

## Slide 15 — OWASP Top 10 (screenshot)

**SAY:** "Every finding automatically maps to the OWASP Top 10 — the industry's standard risk
checklist auditors ask for by name. A03 Injection: 8 findings. A02 Cryptographic Failures: 3.
And on the other side: on **numpy, pandas, pydantic** — clean, mature, heavily-reviewed libraries —
ACR-QA reports **zero high-severity findings. 0.0% false-positive rate on clean code.**"

**SIDE:**
- *OWASP Top 10* = "the globally agreed list of the ten most common ways web systems get hacked."
- *0.0% FP* = "it doesn't cry wolf on clean code." This is your X6 evidence. **SOURCE:**
  `docs/evaluation/REALVULN_BENCHMARK.md` X6 section.

---

## Slide 16 — Attestation: Signature Verified (screenshot)

**SAY:** "Every scan is signed twice — **ECDSA-P256**, the same algorithm used in TLS certificates,
plus a **Dilithium3 post-quantum** signature. The green badge says Signature Verified. Change a
single finding after the fact — the signature breaks instantly. An auditor can verify this exact
scan in one command. This is the provenance evidence the **EU Cyber Resilience Act** requires as
mandatory by September 2026."

**SIDE:**
- *ECDSA* = "a tamper-proof seal." *Post-quantum* = "stays valid even after quantum computers
  break today's encryption." Name it, don't explain the math.
- *EU CRA Sept 2026* = real law, real date, real mandate. **SOURCE:** EUR-Lex Regulation (EU)
  2024/2847 · `docs/PRICING_POSITIONING.md`.
- **SOURCE for attestation code:** `CORE/engines/attestation.py` lines 211–240.

---

## Slide 17 — Competitive Position

**SAY:** "Against Snyk, Semgrep, GitHub Advanced Security: none of them do exploit verification,
none re-test to prove the fix worked, none sign their output cryptographically, none offer an
auto-block tier you can trust. And all are paid or cloud-only. ACR-QA does all five, open-source,
at zero cost. **That open, first-party, in-CI, attested, $0 quadrant is the one the market leaves
empty.** The reason I can make that claim is the Confirmed Tier — without 96.4% precision, you
can't auto-block and the whole story collapses. With it, you can."

**SIDE:**
- Don't trash competitors — "they're excellent at detection; detection is now commoditised. The
  scarce thing is *trust*." That's your column.
- If asked "can't Snyk just add this?" → two moats: open-source means they'd have to open-source
  their own scanner (breaks business model); and every `verification_log` record is proprietary
  ground truth they can't retroactively acquire.

---

## Slide 18 — The Ask (closing)

**SAY:** "Four words. **Trust** — 96.4% Confirmed-Tier precision, high enough to auto-block without
human review. **Proof** — exploit-verified in a sandbox, cryptographically signed — not guesses.
**Reach** — nineteen engines, three languages, nine of ten OWASP, 100% CVE recall. **Price** —
self-hosted, your data never leaves, zero recurring — versus ten to fifty thousand a year. Every
one of those is a measured, sourceable claim. This is not a proposal — it is a running system.
Thank you."

*(Stand still. Smile. Wait.)*

**The one line to remember if you forget everything else:**
> *"Most tools cry wolf. Mine brings you the wolf — then proves the cage holds."*

---

## ⚠️ Number consistency — the reconciled table

If a judge cross-references two slides, these must agree. Know every row.

| Number | What it is | Slide(s) | Source file |
|--------|-----------|----------|-------------|
| **1,942 → 55 @ 96.4%** | Eval corpus (24 repos) funnel | 9 | `ABLATION_STUDY.md` + `FUNNEL_SLIDE.png` |
| **64 / 13 / 4** | payments-api single live scan | 14 | Live DB — run `make seed-demo` |
| **F₁ = 98.2%** | P4 head-to-head | 10 | `HEAD_TO_HEAD.png` + `HEAD_TO_HEAD_BENCHMARK.md` |
| **25.1%** | RealVuln real-world recall | 11 | `REALVULN_LEADERBOARD.png` + arXiv:2604.13764 |
| **100% (8/8)** | Pre-registered CVE recall | 9, 18 | `CVE_RECALL_BATTERY.md` |
| **45%** | AI code shipping a flaw | 2, 4 | Veracode 2025 |
| **+107%** | Vulns/codebase YoY | 2, 4 | Black Duck OSSRA 2026 |
| **3,247 tests** | 3,137 Py + 110 TS | 18 | `pytest --collect-only` + `vitest list` |
| **0.0% FP** | X6 clean packages | 15 | `REALVULN_BENCHMARK.md` X6 |
| **EU CRA Sept 2026** | Mandatory attestation law | 16 | EUR-Lex Reg (EU) 2024/2847 |

---

## 🛡️ "They will verify every word" — instant source for 10 hardest claims

| If they say... | You say... |
|---|---|
| "Source for 45%?" | "Veracode 2025 GenAI Code Security report — URL is in my presenter notes, stat confirmed pre-presentation." |
| "Source for 107%?" | "Black Duck OSSRA 2026 — open-source vulnerabilities per codebase audit across 947 commercial codebases, November 2024–October 2025." |
| "How do we know 96.4% is real?" | "It's in `docs/evaluation/CONFIRMED_TIER.md` with the full Wilson CI derivation, bootstrap n=10,000 seed 42. The figure is `FUNNEL_SLIDE.png` — same number, same corpus." |
| "Can we verify the RealVuln numbers?" | "Yes — arXiv:2604.13764 is the third-party paper. Their ground truth labels, I don't control. Run `scripts/run_eval.py --realvuln` to reproduce." |
| "You said Semgrep gets 17.5% — did you run it yourself?" | "Yes — on the same 22 apps, using their official Python rules. The methodology is in `REALVULN_BENCHMARK.md`." |
| "Where's the head-to-head methodology?" | "`docs/evaluation/HEAD_TO_HEAD_BENCHMARK.md` — same 30 repos, same 8 CVE targets, Semgrep with community rulesets p/default+p/python+p/js+p/go." |
| "How do I know the exploit verification works?" | "Run the exploit suite: `.venv/bin/pytest TESTS/ -m exploit -v` with Docker running. 5/5 pass — SQLi confirmed exploitable, safe code confirmed UNexploitable." |
| "Can I verify the attestation?" | "Yes: `python scripts/verify_attestation.py <bundle.json>` — ECDSA verification against the embedded public key. Try altering a number in the JSON first." |
| "How is the confidence interval computed?" | "Wilson proportion CI, n=55 P4 findings, p̂=0.964, α=0.05, 10,000 bootstrap resamples, seed 42. Formula in `CONFIRMED_TIER.md`." |
| "Why only 25% recall if you claim it's good?" | "Semgrep gets 17.5%, Snyk 17.4%, SonarQube 6.5% on the same benchmark. 25.1% leads the field. The ceiling is ~37–48% because a third of real-world CVEs are auth/CSRF/IDOR — undecidable by Rice's theorem for any static tool." |
