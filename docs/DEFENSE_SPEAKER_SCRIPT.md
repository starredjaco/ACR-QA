# ACR-QA — Defense Speaker Script (15 slides · KSIU template)

**Maps 1:1 to `scripts/build_template_deck.py`** — 16 slides. Target: **~12 min** talk + **3 min** demo = **~15 min total**.
~40–50 seconds per slide. Demo falls between Slides 9 and 10.

**How to read:**
- **SAY** = near-word-for-word. **Bold** = land these slowly.
- **SIDE** = plain-English explanation for non-technical judges + "source?" answer for skeptics.
- **SOURCE** = the exact file/URL to cite if challenged. Know these.

> **The golden rule:** first sentence always needs zero background. Lead plain-English, add depth.
> **The kill line:** *"Most tools cry wolf. Mine brings you the wolf — then proves the cage holds."*

---

## Slide 1 — Title

> **Dr. Samy's mandate — fixed opening.** Read the title slide *exactly as written* — your name, the
> project title, the supervisor — **no more, no less.** Do NOT start explaining or selling on slide 1.
> Introduce, then move to the outline. (*"بتقرأ بالضبط الـ title name بتاع البروجيك بتاعك … من غير
> أي كلمة زيادة ولا كلمة قليلة"*)

**SAY (verbatim, ~15 sec):** "Good morning. My name is **Ahmed Mahmoud Abbas**. My graduation project
is **ACR-QA — Automated Code Review & Quality Assurance**, under the supervision of **Dr. Samy
AbdelNabi**. Thank you for your time — I'll take about fifteen minutes."

**SIDE:**
- Read the title as printed; resist the urge to pitch here — the hook comes on slide 3.
- One breath, then advance to slide 2. Don't linger.

---

## Slide 2 — Presentation Outline

**SAY:** "Here is the roadmap for today. Eight sections: **Introduction** — why AI-written code is
the right problem right now. **Problem Statement** — three reasons teams can't trust automated review.
**Solution** — what ACR-QA is and the three design decisions that make it work. **Methodology** —
how the system is built. **Results and Evaluation** — the numbers, including a live demo. **Use Cases**
— who benefits. **Future Work** — honest gaps and the roadmap. And **Conclusion**."

**SIDE:**
- Eight sections in order: Introduction → Problem → Solution → Methodology → Results → Use Cases
  → Future Work → Conclusion. Name each one as you point at it.
- ~15 seconds — name the eight, don't elaborate yet.

---

## Slide 3 — Introduction

**SAY:** "AI now writes about a third of new enterprise code. The number is rising fast —
and **45% of AI-written code ships with a known security flaw**. That is Veracode's 2025 study,
real codebases, not a survey. Meanwhile, open-source vulnerabilities per codebase **jumped 107% in
one year** — Black Duck OSSRA 2026. And the tooling to catch this costs enterprise teams
**ten to fifty thousand dollars a year**. So your scanner flags nineteen hundred issues, the team
cannot review them all, and **nobody can tell you which one breaches you**. ACR-QA answers that
question with three capabilities: **Detect** — nineteen engines across three languages. **Prove**
— exploit-verified in a real sandbox. **Sign** — every scan is cryptographically attested."

*(Point to the live dashboard screenshot on the right as you say "running system.")*

**SIDE:**
- *45%* — **SOURCE:** Veracode 2025 GenAI Code Security report.
- *+107%* — **SOURCE:** Black Duck OSSRA 2026, SC Media coverage.
- *$10–50k* — **SOURCE:** Snyk/Semgrep/SonarQube public pricing pages.
- The dashboard screenshot on the right is the live running system — not a mockup.

---

## Slide 4 — Problem Statement

**SAY:** "Three reasons teams cannot trust automated review today. First: **quality variance** —
a human reviewer is inconsistent; the SQL injection on line 47 slips through on the fiftieth PR
of the day. Second: **cost** — enterprise tools cost ten to fifty thousand dollars a year, which is
unaffordable for universities and most startups. Third: **hallucination** — AI explainers invent
confident, wrong advice. A developer gets burned once and never trusts the tool again."

**SIDE:**
- *Hallucination* = smoke-alarm analogy: "after enough false alarms, you take out the battery —
  and miss the real fire."
- **SOURCE for $10–50k:** `docs/PRICING_POSITIONING.md` + public pricing pages.

---

## Slide 5 — Solution — ACR-QA

**SAY:** "ACR-QA is a trust layer on top of your existing scanners. One question at merge time:
*is this finding real enough to stop a release on its own?* Three design decisions answer it.
**Confirmed Tier** — four gates: HIGH severity, a 22-rule security set, production code path,
and Bandit HIGH confidence. That combination reaches **96.4% precision — safe to auto-block
without a human in the loop.** **Exploit Verification** — we don't claim a vulnerability, we
detonate it. A Docker sandbox fires a real payload, then fires it again after the AI patch —
it must now fail. Binary ground truth, not static re-analysis. **Cryptographic Attestation** —
every scan is ECDSA-P256 and Dilithium3 signed as a tamper-evident bundle. EU Cyber Resilience
Act compliance out of the box, at zero recurring cost."

**SIDE:**
- Three cards map to three committee questions: "how precise?" / "how do you know it's real?" /
  "how do you prove it later?"
- "Safe to auto-block" = the key claim. Everything else in the presentation justifies this one line.
- **SOURCE:** `docs/evaluation/CONFIRMED_TIER.md` · `CORE/engines/exploit_verifier.py` · `CORE/engines/attestation.py`.

---

## Slide 6 — Methodology: System Architecture

**SAY:** "The system end-to-end. A developer pushes code — the webhook triggers a Celery worker.
**Nineteen engines run across three language adapters**: Ruff, Semgrep, Bandit, and twelve more
for Python; ESLint for JavaScript; staticcheck for Go. Every tool's output is converted into one
common format — the CanonicalFinding — so nothing downstream sees raw tool noise. Then the trust
gates: confidence scoring, reachability, taint analysis, and the Confirmed Tier. The AI retrieves
the rule from a local knowledge base and explains it — it cannot hallucinate because I hand it
the answer first. Everything is stored, signed, and posted back. **Fourteen to ninety seconds,
end to end.**"

**SIDE:**
- *"One common format"* = different tools speak different languages; I translate them into one
  Pydantic schema so I can reason across tools. `CORE/engines/normalizer.py`.
- *"In parallel"* = fast AND independent — no tool's noise pollutes another.
- *"Retrieves the rule"* = RAG: Retrieval-Augmented Generation. Open-book exam — can't invent.
- **SOURCE:** `ACR-QA-Book/figures/arch_overview.png` — generated from `arch_overview.puml`.

---

## Slide 7 — Methodology: Exploit Verification

**SAY:** "This is what makes ACR-QA different from every other tool. **We don't claim a
vulnerability — we detonate it.** Four phases. Phase 1: the rule maps to an exploit category —
SQL injection, command injection, template injection, thirteen categories total. Phase 2: a Docker
container spins up — isolated, one hundred and twenty-eight megabytes of memory, destroyed in
thirty seconds — a real payload fires: `' OR 1=1`, `{{7×7}}`. Attack confirmed. Phase 3: the AI
generates a fix. The **same exact payload fires again against the patched code** — it must now
*fail*. If it still works, the fix is wrong. Phase 4: the vulnerability proof, the fix diff, and
the re-exploit proof are bundled and signed as one ECDSA-P256 + Dilithium3 chain. Verified live:
five out of five exploit tests — SQL injection and SSTI fire; clean code is proven UN-exploitable."

**SIDE:**
- *"Same payload must fail"* = this is what Snyk cannot do. They retest statically. We retest
  with the live exploit — binary ground truth.
- *Dilithium3* = NIST-standardised post-quantum algorithm (2024). Stays secure against quantum
  computers. Name it, don't explain the math.
- **SOURCE:** `CORE/engines/exploit_verifier.py` · `TESTS/ -m exploit` (5/5 pass with Docker).

---

## Slide 8 — Results: The Precision Funnel  ⭐

**SAY:** "Core result. On our **thirty-repository adversarial corpus**, the tools produced
**1,942 raw findings** — at that level only 8.6% are real. We filter: HIGH severity, then our
twenty-two-rule confirmed set, then production code path, then Bandit HIGH confidence. We land on
**55 findings in the Confirmed Tier at 96.4% precision** — with **100% CVE recall preserved at
every step.** Look at the right column: green all the way down. We throw away the noise without
throwing away the real bugs. That **52-percentage-point F₁ margin over Semgrep** is what makes
the auto-block safe."

> **Say this out loud:** "These numbers — 1,942 and 55 — are the evaluation corpus, thirty repos
> combined. The live demo you are about to see is one smaller app, so its confirmed count will be
> proportionally smaller. Same filter, smaller input."

**SIDE:**
- *96.4% precision* vs *100% recall* — two different questions, not contradictory. Know this cold.
- **SOURCE:** `FUNNEL_SLIDE.png` · `docs/evaluation/CONFIRMED_TIER.md` (Wilson CI, 10k bootstrap).
- **SOURCE for 52 pp:** `docs/evaluation/HEAD_TO_HEAD_BENCHMARK.md`.

---

## Slide 9 — Results & Evaluation

**SAY:** "Six measured claims. Confirmed-Tier precision: **96.4%**, 95% confidence interval
90.9 to 100. CVE recall: **100% — 8 of 8** pre-registered targets caught. Head-to-head F₁:
**98.2% versus Semgrep's 45.7%** on the same corpus. And on the **RealVuln 2026 leaderboard** —
real production Python apps with known CVEs, third-party ground truth I did not author —
ACR-QA scores **25.1%**, leading Bandit, Semgrep, Snyk, and SonarQube. OWASP Top 10 coverage:
nine of ten categories. Test suite: 3,247 tests at 88% CORE coverage. And I'll tell you why
RealVuln isn't higher: a third of real-world CVEs — auth logic, CSRF, IDOR — cannot be detected
by any static tool. Rice's theorem. I report the full-corpus number because hiding it would be
dishonest."

*(Advance to demo after this slide.)*

**SIDE:**
- Own the 25.1%. Flip it: "Semgrep gets 17.5%. SonarQube gets 6.5%. I'm leading the field on
  the hardest real-world test available."
- **SOURCE:** `REALVULN_LEADERBOARD.png` · arXiv:2604.13764.
- **SOURCE for 8/8 CVE:** `docs/evaluation/CVE_RECALL_BATTERY.md`.

---

## — LIVE DEMO (between Slides 9 and 10) —

**SAY:** "Let me show you instead of telling you."

*(Switch to the live dashboard. Follow `docs/DEFENSE_DEMO_SCRIPT.md`.)*

**The six-stop path:**
1. **Fleet view** — show recognised repos (requests, httpx, FastAPI). Point to Trust Layer banner.
2. **payments-api run** — 64 findings, 13 high-severity.
3. **Toggle Confirmed Tier** → 4 findings remain. *"The funnel in miniature, on real data, in front of you."*
4. **Click any finding** — show canonical rule ID, confidence, evidence snippet, RAG explanation.
5. **Compliance tab** — OWASP Top 10 breakdown live.
6. **Attestation tab** — "Signature Verified" green badge. *"Tamper one character — it breaks instantly."*

**Recovery if something breaks:**
- Dashboard not loading → open pre-seeded screenshots in `docs/presentation_assets/shots/`.
- DB empty → `make seed-demo` (pre-run before the defense, takes 2 min).
- API 500 → "The findings are pre-stored. Let me show the attestation bundle directly."

---

## Slide 10 — Use Cases: Education & Startups

**SAY:** "Two people who cannot solve this with existing tools. **A university instructor** grading
hundreds of student repositories a term. Enterprise scanners cost ten to fifty thousand dollars —
completely out of reach. ACR-QA is free and self-hosted: it surfaces the real SQL injection without
drowning in style noise, and the RAG explanation *teaches* the student why it is wrong — the tool
does the teaching. **A startup tech lead** shipping dozens of AI-written pull requests a day. They
need an auto-block at merge that will not cry wolf, and a signed audit trail for the EU Cyber
Resilience Act — mandatory by September 2026. That is the 96.4% Confirmed Tier and the ECDSA
attestation, at zero recurring cost."

**SIDE:**
- Lead with whichever judge is in the room — academic committee = start with the instructor.
- *EU CRA Sept 2026* is a hard regulatory deadline. Real law, real date.

---

## Slide 11 — Use Cases: Open Source & Enterprise

**SAY:** "Two more. **An open-source maintainer** reviewing drive-by pull requests from strangers —
no time, no budget. Can they trust a contribution from someone they've never met? Exploit-verified
findings plus signed provenance means you can *trust the contribution without trusting the
contributor*. And **an enterprise security auditor** who must prove to regulators what was scanned,
when, and what was found — months later, tamper-free. Every ACR-QA scan is ECDSA-P256 plus
Dilithium3 signed. One command to verify the entire chain. EU CRA-ready provenance out of the box."

**SIDE:**
- OSS persona = the supply-chain attack angle. Timely — Log4Shell, XZ Utils, polyfill.js.
- Enterprise persona = the compliance angle. This is who *buys* security tools at scale.

---

## Slide 12 — Future Work

**SAY:** "Four honest gaps I identified and plan to close. **Inter-procedural taint analysis** —
tracing tainted data across files and functions, worth an estimated 10 to 15 percentage points of
recall. **More languages** — Java, C#, and Rust adapters. **A managed offering** — a one-click
GitHub App so teams adopt the trust layer without self-hosting. **Independent expert labelling**
— a multi-annotator ground-truth study to harden the precision numbers further. These are not
weaknesses I am hiding — they are the research roadmap."

**SIDE:**
- "These are not weaknesses I am hiding" = the committee respects honesty about scope more than
  pretending the system is complete. Name the gap before they do.

---

## Slide 13 — Conclusion

**SAY:** "Four words. **Trust** — 96.4% Confirmed-Tier precision, high enough to auto-block
without a human review. **Proof** — exploit-verified in a sandbox, cryptographically signed —
not guesses. **Reach** — nineteen engines, three languages, nine of ten OWASP categories,
100% CVE recall. **Price** — self-hosted, your data never leaves, zero recurring — versus ten
to fifty thousand a year. Every one of those is a measured, sourceable claim. The open, attested,
zero-cost quadrant that the market currently leaves empty. This is not a proposal. **It is a
running system.**"

*(Pause. Hold eye contact.)*

> **The kill line:** *"Most tools cry wolf. Mine brings you the wolf — then proves the cage holds."*

**SIDE:**
- "Not a proposal, it is a running system" — the strongest four words of the defense.
- Gemini_6 open-quadrant photo on the right is the visual anchor for "market gap."

---

## Slide 14 — Any Questions?  ← section closer (dark slide)

**SAY:** "I'm happy to go deeper on any number, any slide."

*(Stand still. Smile. Breathe. Let the silence land.)*

---

## Slide 15 — Thank You  ← section closer (dark slide, Gemini_2 hero)

**SAY (only if prompted, otherwise just bow):** "Thank you — Ahmed Mahmoud Abbas, supervised by
Dr. Samy Abdel Nabi."

---

## Number consistency table — know every row

If a judge cross-references two slides, these must agree. Know every row cold.

| Number | What it is | Slide | Source file |
|--------|-----------|-------|-------------|
| **1,942 → 55 @ 96.4%** | Eval corpus (30 repos) funnel | 8 | `ABLATION_STUDY.md` + `FUNNEL_SLIDE.png` |
| **52 pp F₁ margin** | F₁ margin vs Semgrep (98.2% − 45.7%) | 8 | `HEAD_TO_HEAD_BENCHMARK.md` |
| **25.1%** | RealVuln real-world recall | 9 | `REALVULN_LEADERBOARD.png` · arXiv:2604.13764 |
| **100% (8/8)** | Pre-registered CVE recall | 8, 9 | `CVE_RECALL_BATTERY.md` |
| **64 / 13 / 4** | payments-api live scan | Demo | Live DB — run `make seed-demo` |
| **45%** | AI code shipping a flaw | 3 | Veracode 2025 |
| **+107%** | Vulns / codebase YoY | 3 | Black Duck OSSRA 2026 |
| **3,247 tests · 88%** | Test count + CORE coverage | 9 | `pytest --collect-only` + `coverage` |
| **0.0% FP** | X6 clean packages | Demo / Q&A | `REALVULN_BENCHMARK.md` X6 |
| **EU CRA Sept 2026** | Mandatory attestation law | 10, 11 | EUR-Lex Reg (EU) 2024/2847 |
| **96.4% CI 90.9–100%** | Wilson proportion CI | 9 | `CONFIRMED_TIER.md` (Wilson, 10k bootstrap, seed 42) |
| **5/5 exploit tests** | Docker exploit verification | 7, Demo | `pytest -m exploit` with Docker |

---

## "They will verify every word" — instant source for the 10 hardest claims

| If they say… | You say… |
|---|---|
| "Source for 45%?" | "Veracode 2025 GenAI Code Security report — URL in my presenter notes, confirmed pre-defense." |
| "Source for 107%?" | "Black Duck OSSRA 2026 — 947 commercial codebases, November 2024–October 2025. SC Media covered it." |
| "How do we know 96.4% is real?" | "It is in `docs/evaluation/CONFIRMED_TIER.md` with the full Wilson CI derivation, bootstrap n=10,000, seed 42. Same number, same corpus as the funnel figure." |
| "Can we verify the RealVuln numbers?" | "Yes — arXiv:2604.13764 is the third-party paper. Their ground-truth labels, I do not control. Run `scripts/run_eval.py --realvuln` to reproduce." |
| "You said Semgrep gets 17.5% — did you run it yourself?" | "Yes — on the same 22 apps, same rules, same matching criteria. Methodology is in `REALVULN_BENCHMARK.md`." |
| "Where is the head-to-head methodology?" | "`docs/evaluation/HEAD_TO_HEAD_BENCHMARK.md` — same 30 repos, same 8 CVE targets, Semgrep with official rulesets p/default+p/python+p/js+p/go." |
| "How do I know the exploit verification works?" | "Run `.venv/bin/pytest TESTS/ -m exploit -v` with Docker running. 5/5 pass — SQLi confirmed exploitable, safe code confirmed UN-exploitable." |
| "Can I verify the attestation?" | "Yes: `python scripts/verify_attestation.py <bundle.json>` — ECDSA verification against the embedded public key. Alter one character first and watch it break." |
| "How is the confidence interval computed?" | "Wilson proportion CI, n=55 Confirmed-Tier findings, p̂=0.964, α=0.05, 10,000 bootstrap resamples, seed 42. Formula in `CONFIRMED_TIER.md`." |
| "Why only 25% recall if you claim it is good?" | "Semgrep gets 17.5%, Snyk 17.4%, SonarQube 6.5% on the same benchmark. 25.1% leads the field. The ceiling is ~37–48% because a third of real-world CVEs are auth/CSRF/IDOR — undecidable by Rice's theorem for any static tool." |

---

## Expected Q&A — Concept Questions (30-second answers)

*Full explanations are in `docs/QA_PREP.md` §SQ1–SQ9. Memorise the one-liner here; go to QA_PREP for depth.*

---

**Q: "Who is Veracode and why should I trust that 45% stat?"**

> "Veracode scans millions of real enterprise codebases every year — not a developer survey, actual
> code. Their 2025 State of Software Security report found 45% of codebases with AI-generated code
> contained at least one known flaw. It is in my bibliography, independently covered by SC Media and
> Dark Reading."

---

**Q: "What is Black Duck OSSRA and where does +107% come from?"**

> "Black Duck is Synopsys's open-source auditing division. OSSRA is their annual audit of thousands
> of commercial codebases. The 2026 edition found vulnerability counts per average codebase more than
> doubled year-over-year. Alerts doubled while teams did not. That is why precision matters."

---

**Q: "You said 1,942 issues — why does the dashboard show a different number?"**

> "These are two different views. 1,942 is the evaluation corpus across 30 repos, measured in the
> controlled benchmark, never changes. The dashboard shows the rolling live scan total for whatever
> repos are seeded — a different, smaller dataset. Same filter logic, different input. The demo
> makes it concrete: toggle Confirmed Tier on payments-api — 64 raw findings become 4. That is the
> funnel in miniature."

---

**Q: "Why are there two numbers — 96.4% and 91%? What is triage vs auto-block?"**

> "Same scan, two settings — like a car's 0-to-60 versus its fuel economy. Both true, neither
> contradicts the other.
>
> Full Output (91% recall): catches 91 of every 100 real bugs. Noisy — needs a human to sort. That
> is triage — an ER doctor sorting patients by urgency. OK to have false alarms because a human filters them.
>
> Confirmed Tier (96.4% precision): only findings that pass all 4 gates. 96 out of 100 are real.
> That is auto-block — a fire door that closes on smoke, no human needed. You can only do that if
> precision is near-perfect, otherwise developers learn to override it."

---

**Q: "What is ECDSA-P256? What is post-quantum? What does tamper-evident mean?"**

> "ECDSA-P256 is the same algorithm behind every HTTPS padlock in your browser. ACR-QA computes a
> fingerprint of all findings and locks it with a private key. Anyone with the public key can verify
> it — if one character changes afterwards, verification fails instantly. That is tamper-evident —
> like a notary stamp.
>
> Dilithium3 is a post-quantum signature — NIST standardised it in 2024. It stays secure even
> against quantum computers. The EU CRA requires this class of provenance by September 2026.
> ACR-QA already implements it."

---

**Q: "Is the architecture diagram really your system? Did you draw it or copy it?"**

> "It is generated from source code in the repo — `ACR-QA-Book/figures/arch_overview.puml`, a
> PlantUML text file with months of git history. Every box maps to a real directory and a real
> Python file. The 3,247 tests prove those boxes execute real code."

---

**Q: "Explain the exploit verification — what actually happens?"**

> "Four phases.
>
> Phase 1 DETECT: the scanner flags a finding. The rule maps to one of 13 exploit categories.
>
> Phase 2 DETONATE: a Docker container spins up — isolated, 128MB, destroyed in 30 seconds. A real
> payload fires: `' OR 'canary'='canary' --` for SQLi. The database returns unauthorised data.
> Attack confirmed.
>
> Phase 3 PATCH: the AI generates a fix — parameterised queries for SQLi. The same payload fires
> against the patched code. It must FAIL. If it still works, the AI retries.
>
> Phase 4 SIGN: vulnerability proof + fix diff + re-exploit proof are bundled and signed. One
> command verifies the whole chain.
>
> Snyk and Semgrep reanalyse statically after a fix. We re-fire the live exploit. Binary ground
> truth — it either works or it does not."

---

**Q: "How do I know Snyk and Semgrep do not do exploit verification?"**

> "Search docs.snyk.io, docs.semgrep.dev, docs.github.com/en/code-security for Docker sandbox
> exploit detonation. It does not exist in any of them. Snyk publishes roughly 85% precision for
> their high-confidence tier. Semgrep's conservative precision on my HEAD_TO_HEAD corpus is 36%.
> Neither claims 96%+. And neither re-fires the live payload against the patched code."

---

**Q: "Who are Snyk, Semgrep, and GitHub Advanced Security?"**

> "Three market segments.
>
> Snyk — New York, 2015. Biggest developer-security brand, $7.4B peak valuation, used by Google
> and Salesforce. The most common answer to 'what scanner do you use?'
>
> Semgrep — San Francisco, 2020. Developer-first open-source static analysis. Actually embedded
> inside ACR-QA as one of the 19 engines — the comparison shows what the aggregation layer adds.
>
> GitHub Advanced Security — Microsoft, 2020. Uses CodeQL, developed at Oxford. The reference a
> university committee will recognise. My evaluation uses the same methodology CodeQL papers use.
>
> I picked all three because they cover every segment. Outperforming all three on five specific
> capabilities is the whole competitive argument."
