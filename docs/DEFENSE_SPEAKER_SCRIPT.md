# ACR-QA — Defense Speaker Script (with plain-English side notes)

**Maps 1:1 to `docs/ACR-QA_Defense.pptx` (20 slides).** Target: **12–15 minutes** of talking +
**5 minutes** live demo. ~40 seconds per slide.

**How to read this doc:**
- **SAY** = what you say, near-word-for-word. **Bold** = phrases to land slowly and clearly.
- **SIDE** = the plain-English meaning of every number/term on that slide — for the non-technical
  judge, and so *you* can answer "what does that mean?" instantly. This is your safety net.

> **The golden rule for a mixed room:** every answer's *first sentence* needs zero background.
> Lead plain-English, then add the technical depth. The numbers below are all reconciled — the
> same figure means the same thing on every slide, in the demo, and in Q&A. (See the
> "Number consistency" box at the end — memorise it; it's how you survive "are you making this up?")

---

## Slide 1 — Title

**SAY:** "Good morning. I'm Ahmed. My project is **ACR-QA** — an automated code-review platform
that doesn't just *find* security bugs, it *proves* which ones are real. Over the next fifteen
minutes I'll show you the problem, what I built, the results, and a live demo where you'll watch
it attack a real vulnerability and then prove the fix holds."

**SIDE:** *Set the frame: this is a "trust" tool, not "another scanner." Say the word "prove"
twice — it's the whole thesis. Don't rush; let them read the title.*

---

## Slide 2 — The Hook

**SAY:** "AI now writes about a third of new code. But **45% of AI-written code ships with a known
security flaw** — that's Veracode's 2025 study. And the number of vulnerabilities in a typical
codebase **jumped 107% in a single year** — Black Duck's 2026 report. So your scanner now flags
nineteen hundred issues per project. **Which one breaches you?** Nobody can review that — so teams
either ship blind, or pay fifty thousand a year and *still* don't trust the output."

**SIDE:**
- *45% (Veracode 2025 GenAI report)* = "almost half of the code AI writes has a hole in it."
- *+107% (Black Duck OSSRA 2026)* = "the pile of alerts doubled in one year."
- **If asked "source?":** name Veracode 2025 and Black Duck OSSRA 2026 — both are in your presenter
  notes. *These are the two numbers you must be able to source on demand — they anchor the sell.*
- Takeaway for the non-technical judge: "more code, more holes, more noise, less trust."

---

## Slide 3 — Outline

**SAY:** "Here's the path: the problem and the market, the solution and its core ideas, the
architecture, then the part that matters most — **how we go from noise to trust** — the results,
a live demo, and where this sits competitively."

**SIDE:** *Ten seconds. Point at "Evaluation" and "Live demo" (the green ones) — "those two are
where I'd focus your attention." Then move on.*

---

## Slide 4 — The Problem

**SAY:** "Three reasons teams can't trust automated review today. **One — quality variance:** a
human reviewer is inconsistent; the SQL injection on line 47 slips through on the fiftieth pull
request of the day. **Two — cost:** enterprise tools are ten to fifty thousand a year, so
universities and startups run a basic linter or nothing. **Three — hallucination:** AI explainers
invent confident, wrong advice; a developer gets burned once and never trusts the tool again."

**SIDE:**
- *"Hallucination"* for a non-technical judge = "the AI makes things up and says them confidently."
- This slide is the *enemy*. Each card is a problem ACR-QA later kills: variance → automation;
  cost → $0 self-hosted; hallucination → RAG grounding. You'll call back to these.

---

## Slide 5 — The Market Reality

**SAY:** "The same story as numbers. Enterprise scanners: **ten to fifty thousand dollars a year.**
Vulnerabilities per codebase: **up 107%.** AI-written code shipping a flaw: **45%.** ACR-QA:
**zero** — self-hosted, no licence, your data never leaves your machine."

**SIDE:**
- This is the "**why now, why pay attention**" slide. The contrast is the sell: the risk is
  *rising* (107%, 45%) while the fix is *expensive* ($10–50k) — except mine is **$0**.
- *$0 doesn't mean "cheap and worse" — say "self-hosted," which to a technical judge means
  "no data leaves, no subscription," a real enterprise selling point (privacy + cost).*

---

## Slide 6 — The Solution: ACR-QA

**SAY:** "ACR-QA is a **trust layer that sits on top of your existing scanners**. At merge time it
answers one question: *is this finding real enough to block automatically?* Four ideas make that
work. It uses **RAG-grounded AI** — the explanation cites the actual rule instead of guessing. It
has a **Confirmed Tier** — a strict filter that's 96.4% precise, accurate enough to auto-block. It
**verifies exploits** — it detonates a real attack in a sandbox, so it's proven, not claimed. And
every scan is **cryptographically signed** — tamper-proof and auditable. All of it on-premises, at
zero recurring cost."

**SIDE:**
- *RAG* = "before the AI explains, I hand it the official rule text, so it can only rephrase facts,
  not invent them." Analogy: *open-book exam — it can't make up an answer.*
- *Confirmed Tier* = "the small set of findings I'm so sure about, the system can block the code by
  itself." *96.4% precise = "out of 100 it flags here, ~96 are real bugs."*
- *Exploit verification* = "it actually breaks in, to prove the bug is real." Analogy: *a locksmith
  who picks the lock to prove it's pickable — not a guess.*
- *Attestation/signed* = "a tamper-proof receipt, like a notary stamp, so nobody can fake the result later."

---

## Slide 7 — Live Dashboard (Overview screenshot)

**SAY:** "This is the real running dashboard — not a mockup. It's already scanned a fleet of
projects, including open-source libraries you'll recognise: **requests, httpx, FastAPI, Flask.**
The green banner across the top shows the live trust metrics. This is the actual product; you'll
see it live in a few minutes."

**SIDE:**
- *Stress "real, not a mockup" — committees assume student demos are faked.* The famous repo names
  (requests/FastAPI) are your credibility: "I ran it on code the whole industry uses."
- If they ask "is the data real?" → "Yes — real tools, real findings, on real open-source code."

---

## Slide 8 — System Architecture

**SAY:** "End to end: a push triggers a webhook, we pull the changed code, and queue it. The
detection layer runs **six tools in parallel** — Ruff, Semgrep, Bandit and others. Every tool's
output is normalised into **one common format** so nothing downstream sees raw tool noise. Then the
trust gates: confidence scoring, reachability, taint tracking, the Confirmed Tier, and exploit
verification. The AI retrieves the rule and explains it. Everything is stored, signed, and posted
back as PR comments. **Thirty to ninety seconds per pull request.**"

**SIDE:**
- *"Normalise into one format"* = "different tools speak different languages; I translate them all
  into one, so I can reason about them together." (This is the `CanonicalFinding` — the engineering
  backbone. A technical judge will respect this.)
- *"In parallel"* = fast; *"taint tracking"* = "following the user's input to see if it reaches a
  dangerous place." Analogy: *tracing a dye through pipes to see where it ends up.*
- Don't read all six tool names slowly — group them: "six analyzers at once."

---

## Slide 9 — The Precision Funnel  ⭐ (the heart — and the slide most likely to trip you)

**SAY:** "This is the core idea, measured on our **full benchmark evaluation**. The tools produced
**1,942 raw findings** — and at that level only about 9% are real; that's the noise everyone drowns
in. We filter by severity, then by a curated security rule set, then a taint gate — and we land on
**55 findings in the Confirmed Tier, at 96.4% precision**, with **100% of the known CVEs still
caught** at every step. That's the whole thesis in one picture: **we throw away the noise without
throwing away the real bugs.**"

**SIDE — READ THIS, it's the trap:**
- **These 1,942 → 55 numbers are the EVALUATION CORPUS** (many vulnerable apps with known answers).
  **They are NOT the payments-api you'll demo live.** In two slides the live demo shows a *single*
  repo with **4** confirmed findings — a small number *because it's one small app.* **Pre-empt it:**
  say *"the funnel is the full benchmark; the live scan you'll see is just one repo, so its confirmed
  count is small."* If you don't say this and a judge sees 55 here and 4 there, it looks like a lie.
- *96.4% precision* = "96 of every 100 it confirms are real." *100% CVE recall* = "of the known
  planted bugs, it missed none." *Two different things — precision is 'am I right when I flag?',
  recall is 'did I catch them all?'* (You'll get asked the difference — that's the one-liner.)

---

## Slide 10 — Evaluation & Results

**SAY:** "The numbers behind that. Confirmed-Tier precision: **96.4%**, with a confidence interval.
Pre-registered CVE recall: **100% — eight of eight detectable.** Head-to-head F1 score: **98%,
versus Semgrep at 46 and Bandit at 22** on the same repos. **Nine of ten** OWASP categories. And on
the 2026 RealVuln real-world benchmark we score **25.1% — beating Semgrep, Snyk, and SonarQube.**"

**SIDE:**
- *"Pre-registered"* = "I wrote down which bugs I expected to catch *before* I ran the test, and
  committed it to version control with a timestamp — so I can't be accused of picking the questions
  after seeing the answers." Analogy: *sealing your prediction in an envelope first.*
- **The 25.1% looks low — own it before they pounce:** "On messy real-world code everybody scores
  low because a third of real bugs can't be caught by *any* static tool. 25% still beats every
  traditional scanner on this benchmark; Semgrep gets 17.5%, SonarQube 6.5%." *Leading with the
  unflattering number is your credibility move.*
- *F1* = "a combined score of being both accurate and thorough." Higher = better.

---

## Slide 11 — Why You Can Trust the Numbers

**SAY:** "Three reasons to trust all this. **One — I separated detection from trust:** most tools
emit 30 to 70% false positives; the Confirmed Tier hits 96.4%. **Two — I don't *claim* a
vulnerability, I *detonate* it:** real payloads in a sandbox — `OR 1=1` for SQL injection, `{{7×7}}`
returning 49 for template injection — and I verified that safe code correctly does *not* fire.
**Three — every result is signed:** ECDSA plus a public transparency log; an auditor verifies the
exact scan in one command."

**SIDE:**
- This slide directly answers "**how do I know you're not lying?**" — every item is a mechanism that
  makes lying *impossible*, not a promise. Say that out loud if it fits: "I built it so I *can't*
  fudge the numbers."
- *"safe code correctly does NOT fire"* is the subtle, important one: "it doesn't just cry wolf —
  I proved that on clean code it stays silent."
- *Transparency log / Rekor* = "a public ledger; once it's written, it can't be quietly changed."

---

## Slide 12 — Live Demo (section divider)

**SAY:** "Let me show you instead of telling you. Real repo, real finding, real exploit — and a
signed receipt at the end."

**SIDE:** *Breathe. Switch to the dashboard/terminal. Follow `docs/DEFENSE_DEMO_SCRIPT.md` for the
5-minute flow. If anything breaks, fall back to the pre-seeded run — the script has recovery lines.
The three screenshots on the next slides are your backup if the live demo dies entirely.*

---

## Slide 13 — Run Detail: payments-api (screenshot)

**SAY:** "This is a single real scan — a sample backend called payments-api. **64 findings, 13
high-severity**, including a genuine SQL injection, an unsafe `eval`, and hardcoded secrets. Every
finding carries its rule, severity, and a confidence score, and the tabs expose compliance,
attestation, and risk."

**SIDE:**
- *This is the "one repo" from the funnel warning.* 64 findings / 13 HIGH / **4 Confirmed Tier** —
  small confirmed count *because it's one small app*, exactly as you flagged on slide 9. Consistent.
- If asked "why only 4 confirmed when the funnel said 55?" → "55 was across the whole benchmark of
  many apps; this is one app. Same filter, smaller input."

---

## Slide 14 — OWASP Top 10 Coverage (screenshot)

**SAY:** "Every finding maps to an OWASP Top 10 category — the industry's standard risk checklist.
Here, real per-category counts for this scan: injection, cryptographic failures, and so on. And the
flip side: on mature libraries like **numpy and pandas, ACR-QA reports zero high-severity findings —
a 0.0% false-positive rate.** On clean code, it stays quiet."

**SIDE:**
- *OWASP Top 10* = "the universally agreed list of the ten most common web security risks." Auditors
  ask for this by name.
- *0.0% FP on numpy/pandas* = "I pointed it at famously clean, heavily-reviewed code and it didn't
  raise a single false alarm." This is your answer to "doesn't it cry wolf?" — *show, don't argue.*

---

## Slide 15 — Cryptographic Attestation (screenshot)

**SAY:** "Finally, the receipt. Every scan is signed twice — a standard **ECDSA** signature plus a
**post-quantum** signature that stays valid even against future quantum computers. The badge says
**Signature Verified**. Change a single finding after the fact and verification fails. This is the
provenance regulators will demand under the EU Cyber Resilience Act this September."

**SIDE:**
- *"Signed"* = "a tamper-proof seal." *"Post-quantum"* = "future-proof against the next generation of
  code-breaking computers" — name-drop only; don't explain lattices unless asked.
- *EU CRA, Sept 2026* = a real, dated law forcing exactly this kind of evidence — your "why this
  matters commercially" hook. *Ties the academic project to a market deadline.*

---

## Slide 16 — Competitive Position

**SAY:** "Where this sits. Against Snyk, Semgrep, and GitHub Advanced Security: none of them do
exploit verification, none re-test to prove the fix worked, none sign their results, none offer an
auto-block tier — and all of them are paid or cloud-only. ACR-QA does all five, open-source, at
zero cost. **That open, first-party, in-CI, attested, $0 quadrant is the one the market leaves
empty.**"

**SIDE:**
- Don't trash competitors — say "they're excellent at detection; detection is now commoditised. The
  scarce thing is *trust*, and that's the column I own."
- *"first-party"* = "scans your own source code, not just your dependencies." *"in-CI"* = "runs
  automatically on every code change."

---

## Slide 17 — Implementation Status

**SAY:** "This is built, not a proposal. **Nineteen analysis engines.** A 52-endpoint API with a
live React dashboard. **Over 3,200 automated tests** — 3,137 Python plus 110 frontend — at 88%
core coverage. Exploit verification across 13 vulnerability classes. Packaged and installable today
as `acrqa` from PyPI, self-hosted, zero recurring cost."

**SIDE:**
- *Test count is 3,247 (3,137 Python + 110 TS) — say "over 3,200." This is the reconciled number;
  it matches the deck. Do NOT say 3,017 or 3,063 — those are stale.*
- *"19 engines"* — if challenged ("I read 36 somewhere"): "19 *detection* engines that produce
  findings; 36 total modules including scoring, explanation, and attestation. Two counting levels,
  not a contradiction." (Full answer in QA_PREP.)

---

## Slide 18 — What ACR-QA Delivers (The Ask)

**SAY:** "Four things to remember. **Trust** — 96.4% precision, high enough to auto-block. **Proof**
— exploit-verified and signed, not guesses. **Reach** — nineteen engines, three languages, nine of
ten OWASP, 100% CVE recall. **Price** — self-hosted, your data never leaves, zero recurring, versus
ten to fifty thousand a year. Every one of those is a measured claim, not a slogan."

**SIDE:** *This is your closing pitch — slow down, one beat per word: Trust. Proof. Reach. Price.
If you forget everything else, these four words ARE the sell.*

---

## Slide 19 — Future Work

**SAY:** "Where it goes next: **inter-procedural taint analysis** — tracing data across functions,
worth an estimated 10–15 points of recall. **Automatic pull-request generation** to apply the fix.
More languages — Java, PHP, Rust. And an **open-core path**: the scanner stays free, a hosted
compliance-evidence tier serves the EU CRA and SOC2 market."

**SIDE:**
- Naming limitations as *planned work* is a strength — it shows you know the boundaries. *"I'd
  rather ship one layer that works than four that half-work."*
- *Inter-procedural* = "right now it follows the data within one function; next, across the whole
  program." Honest, scoped, not a weakness.

---

## Slide 20 — Thank You / Questions

**SAY:** "To summarise: most tools hand you a list and walk away. ACR-QA hands you a list, **proves
which items are real, and signs the proof.** It's not a better scanner — it's a **trust layer**.
Thank you. I'm happy to take questions, or show you any part of the live system."

**SIDE:** *Stop. Smile. Stand still. Let the first question come. For tough questions, lead with the
plain-English sentence, then go deep — and remember the sticky line:* **"Most tools cry wolf. Mine
brings you the wolf — then proves the cage holds."**

---

## ⚠️ Number consistency — memorise this (it's how you answer "are you making this up?")

Every figure below means ONE thing. If a judge cross-checks two slides, they must agree.

| Number | EXACTLY what it is | Where it appears | The trap |
|--------|-------------------|------------------|----------|
| **1,942 → 55** | The **benchmark evaluation** (many vulnerable apps), funnel end-to-end | Slide 9 funnel | NOT one repo — it's the whole corpus |
| **55 @ 96.4%** | Confirmed Tier on that **full benchmark** | Slides 9, 10, 18 | Pairs with "100% CVE recall" |
| **64 / 13 HIGH / 4 confirmed** | The **single payments-api** live scan | Slides 13 + live demo | This is why the live count is "only 4" |
| **25.1%** | RealVuln **real-world** recall (one hard benchmark) | Slide 10 | Low on purpose; beats Semgrep 17.5% |
| **100% (8/8)** | CVE recall on the **detectable** pre-registered set | Slides 10, 18 | "detectable" matters — say it |
| **45%** | AI code shipping a flaw — **Veracode 2025** | Slides 2, 5 | Have the source ready |
| **+107%** | Vulns per codebase YoY — **Black Duck OSSRA 2026** | Slides 2, 5 | Open-source vulns, 2024 |
| **3,247 tests** | 3,137 Python + 110 TS | Slides 10, 17 | Say "over 3,200" — never 3,017/3,063 |
| **19 engines** | *Detection* engines | Slides 17, 18 | 36 = total modules; clarify if asked |

**The one-line defense of all of it:** *"I report every number with the exact corpus it came from,
including the ugly ones — because a liar hides the bad numbers, and I lead with mine."*
