# ACR-QA — Defense Speaker Script (15 slides · photo-first)

**Maps 1:1 to `docs/ACR-QA_Defense.pptx`** (15 slides). Target: **~10 min** talk + **4 min** demo = **~14 min total**.
~40–50 seconds per slide.

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
About fifteen minutes."

**SIDE:** Set the frame: "trust" not "scanner." Say "proves" — it's the whole thesis.

---

## Slide 2 — The Hook

**SAY:** "AI now writes about a third of new enterprise code. And **45% of AI-written code ships
with a known security flaw** — that's Veracode's 2025 study. Meanwhile, open-source vulnerabilities
per codebase **jumped 107% in one year** — Black Duck's 2026 report. And fixing this costs
enterprise teams **ten to fifty thousand dollars a year** in tooling. Your scanner flags nineteen
hundred issues. **Which one breaches you?** Nobody can review that — so teams either ship blind,
or pay fifty thousand a year and still don't trust the output."

**SIDE:**
- *45%* = "almost half of what AI generates has a hole." **SOURCE:** Veracode 2025 GenAI Code
  Security report. URL in presenter notes.
- *+107%* = "the pile of alerts doubled in one year." **SOURCE:** Black Duck OSSRA 2026,
  SC Media coverage. URL in presenter notes.
- *$10–50k* = **SOURCE:** Snyk/Semgrep/SonarQube public pricing pages.
- Never say "1.88×" — that stat was removed because it's unsourceable.

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

## Slide 4 — The Solution: ACR-QA

**SAY:** "ACR-QA is a trust layer on top of your existing scanners. At merge time it answers one
question: *is this finding real enough to block automatically?* One scan, two settings: the
**Confirmed Tier** at 96.4% precision — safe to auto-block — or **Full Output** at 91% recall for
developer triage. Three other innovations make this work. **RAG-grounded AI** — the explanation
cites the actual rule, can't hallucinate. **Exploit verification** — detonates a real attack in an
isolated sandbox. **ECDSA + post-quantum signatures** — every scan is tamper-proof, on-premises,
zero cost."

**SIDE:**
- *"One scan, two settings"* = like a car's 0–60 vs fuel-economy — same car, different measurement
  for different questions. This pre-empts "which number is real?"
- *RAG* = open-book exam: it can't invent an answer because I hand it the rule text first.
- *96.4% precision* = "96 of 100 it flags are real bugs." **SOURCE:** `docs/evaluation/CONFIRMED_TIER.md`.
- *Exploit verification* = the locksmith analogy: *we pick the lock to prove it opens.*
- *Post-quantum* = future-proof against quantum computers. Say the word; don't explain lattices.

---

## Slide 5 — Architecture (FIGURE: arch_overview.png)

**SAY:** "The system end-to-end. A developer pushes code — the webhook triggers a Celery worker.
**Twelve tools run in parallel**: Ruff, Semgrep, Bandit, and the rest. Every tool's output is
converted into one common format — the CanonicalFinding — so nothing downstream sees raw tool noise.
Then the trust gates: confidence scoring, reachability, taint, and the Confirmed Tier. The AI
retrieves the rule and explains it. Everything is stored, signed, and posted back. **Fourteen to
ninety seconds, end to end.**"

**SIDE:**
- *"One common format"* = different tools speak different languages; I translate them into one
  schema so I can reason about them together. The `CanonicalFinding` Pydantic model in
  `CORE/engines/normalizer.py`.
- *"In parallel"* = fast AND independent — no tool's noise pollutes another's.
- **SOURCE:** `ACR-QA-Book/figures/arch_overview.png` — live generated from `arch_overview.puml`.

---

## Slide 6 — Live Dashboard: Fleet Overview (screenshot)

**SAY:** "This is the real running dashboard — not a mockup. It's already scanned a fleet of
projects including open-source libraries you'll recognise: **requests, httpx, FastAPI, Flask.**
The Trust Layer banner shows live KPIs. The Confirmed Tier tile fetches from the API in real time —
it was never estimated or hardcoded. You'll see it live in a few minutes."

**SIDE:**
- Stress "real, not a mockup" — committees assume student demos are faked. Famous repo names are
  your credibility: "I ran it on code the whole industry uses."
- If asked "is it live?" → "yes — API is running on localhost:8000 right now."

---

## Slide 7 — The Precision Funnel (FIGURE: FUNNEL_SLIDE.png)  ⭐

**SAY:** "This is the core result. On our **twenty-four-repository adversarial corpus**, the tools
produced **1,942 raw findings** — at that level only 8.6% are real. We filter by severity, then by
a curated security rule set, then by reachability and taint — and we land on **55 findings in the
Confirmed Tier, at 96.4% precision**, with **100% CVE recall preserved at every step.** Note the
right column — green all the way down. **We throw away the noise without throwing away the real bugs.**
That **52-percentage-point F₁ margin over Semgrep** is what makes the auto-block safe."

**⚠️ PRE-EMPT the trap — say this out loud:**
> "These numbers — 1,942 and 55 — are the *evaluation corpus*, twenty-four repos combined. The
> live scan you're about to see is *one* smaller app, so its confirmed count will be proportionally
> smaller. Same filter, smaller input."

**SIDE:**
- *96.4% precision* vs *100% recall* = two different questions: "am I right when I flag?" vs
  "did I catch them all?" Not contradictory — both measured, both real.
- **SOURCE:** `ACR-QA-Book/figures/FUNNEL_SLIDE.png` · `docs/evaluation/ABLATION_STUDY.md` ·
  `docs/evaluation/HEAD_TO_HEAD_BENCHMARK.md` (for the 52 pp margin).

---

## Slide 8 — RealVuln Leaderboard (FIGURE: REALVULN_LEADERBOARD.png)

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

## Slide 9 — Exploit Verification (FIGURE: verified_remediation.png)

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

## Slide 10 — Live Demo (section divider)

**SAY:** "Let me show you instead of telling you."

*(Switch to dashboard/terminal. Follow `docs/DEFENSE_DEMO_SCRIPT.md`. Three recovery lines if
anything breaks — it's in the script. The pre-seeded runs are your safety net.)*

---

## Slide 11 — Run Detail: payments-api (screenshot)

**SAY:** "One real scan — payments-api, a deliberately-vulnerable backend. **64 findings, 13
high-severity, 4 in the Confirmed Tier** — SQL injection, unsafe eval, hardcoded secrets. Each
finding shows its canonical rule ID, severity, confidence score. Tabs: compliance breakdown,
attestation, PR risk score."

**SIDE:**
- *4 confirmed* vs *55 in the funnel* — you pre-empted this on slide 7. If asked: "55 was across
  twenty-four repos; this is one app. Same filter, smaller input."

---

## Slide 12 — OWASP Top 10 (screenshot)

**SAY:** "Every finding automatically maps to the OWASP Top 10 — the industry's standard risk
checklist auditors ask for by name. A03 Injection: 8 findings. A02 Cryptographic Failures: 3.
And on the other side: on **numpy, pandas, pydantic** — clean, mature, heavily-reviewed libraries —
ACR-QA reports **zero high-severity findings. 0.0% false-positive rate on clean code.**"

**SIDE:**
- *OWASP Top 10* = "the globally agreed list of the ten most common ways web systems get hacked."
- *0.0% FP* = "it doesn't cry wolf on clean code." This is your X6 evidence. **SOURCE:**
  `docs/evaluation/REALVULN_BENCHMARK.md` X6 section.

---

## Slide 13 — Attestation: Signature Verified (screenshot)

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

## Slide 14 — Competitive Position

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

## Slide 15 — The Ask (closing)

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
| **1,942 → 55 @ 96.4%** | Eval corpus (24 repos) funnel | 7 | `ABLATION_STUDY.md` + `FUNNEL_SLIDE.png` |
| **64 / 13 / 4** | payments-api single live scan | 11 | Live DB — run `make seed-demo` |
| **>52 pp F₁ over Semgrep** | F₁ margin (98.2% − 45.7%) on 30-repo corpus | 7 | `HEAD_TO_HEAD_BENCHMARK.md` |
| **25.1%** | RealVuln real-world recall | 8 | `REALVULN_LEADERBOARD.png` + arXiv:2604.13764 |
| **100% (8/8)** | Pre-registered CVE recall | 7, 15 | `CVE_RECALL_BATTERY.md` |
| **45%** | AI code shipping a flaw | 2 | Veracode 2025 |
| **+107%** | Vulns/codebase YoY | 2 | Black Duck OSSRA 2026 |
| **3,247 tests** | 3,137 Py + 110 TS | 15 | `pytest --collect-only` + `vitest list` |
| **0.0% FP** | X6 clean packages | 12 | `REALVULN_BENCHMARK.md` X6 |
| **EU CRA Sept 2026** | Mandatory attestation law | 13 | EUR-Lex Reg (EU) 2024/2847 |

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
| "Which Confirmed-Tier number is the real one?" | "One scan, two settings — like a car's 0–60 vs fuel economy. The 96.4% precision Confirmed Tier auto-blocks; Full Output at 91% recall is the triage view. Both are in slide 4." |
