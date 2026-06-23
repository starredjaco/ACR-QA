# ACR-QA — Defense Speaker Script (21 slides · KSIU template)

> **✅ POST-DEFENSE (2026-06-24):** this reflects the defense delivered 2026-06-19 and is kept as the
> historical record. The engine has since reached **#1 on recall on RealVuln 2026 — 58.8%** (official,
> edging out GPT-5.5 58.2% at $0; held-out 53.0%; deterministic 80.6%-precision Confirmed tier; real
> post-quantum Dilithium3). Use 58.8% (not 25.1%/50%) for any reuse. See
> `../evaluation/REALVULN_PURE_STATIC_2026_06_22.md` (path-adjust as needed).

**Maps 1:1 to `scripts/build_template_deck.py`** — 21 slides. Target: **~13 min** talk, then a **2–3 min
live demo AFTER you finish** (not in the middle). Photo slides run fast (~20–25 s); diagram slides get
the time (~50 s). **The full demo walkthrough is at the very end — see "POST-PRESENTATION DEMO."**

**How to read:**
- **SAY** = near-word-for-word. **Bold** = land these slowly.
- **SIDE** = plain-English explanation for non-technical judges + "source?" answer for skeptics.
- **SOURCE** = the exact file/URL to cite if challenged. Know these.

> **The golden rule:** first sentence always needs zero background. Lead plain-English, add depth.
> **The kill line:** *"Most tools cry wolf. Mine brings you the wolf — then proves the cage holds."*
> **The identity line (say it whenever AI comes up):** *"ACR-QA's TRUST is deterministic — it detonates a real
> exploit to prove the bug and cryptographically signs the result. That's proof no LLM can give."*
> **Go QUIET on the LLM** — don't headline it, never claim "no AI." If asked, see the honest answer on Slide 20.

---

## Slide 1 — Title

> **Dr. Samy's mandate — fixed opening.** Read the title slide *exactly as written* — your name, the
> project title, the supervisor — **no more, no less.** Do NOT start explaining or selling on slide 1.

**SAY (verbatim, ~15 sec):** "Good morning. My name is **Ahmed Mahmoud Abbas**. My graduation project
is **ACR-QA — Automated Code Review & Quality Assurance**, under the supervision of **Dr. Samy
AbdelNabi**. Thank you for your time — I'll take about fifteen minutes."

**SIDE:** Read the title as printed; the hook comes on slide 3. One breath, then advance.

---

## Slide 2 — Presentation Outline

**SAY:** "Here is the roadmap. **Introduction** — why AI-written code is the right problem now.
**Problem Statement** — three reasons teams can't trust automated review. **The Solution** — ACR-QA
and its four pillars. **System Architecture** — how it's built. **Evaluation and Data** — what we
tested against. **Results**, including a live demo. **Use Cases** — who benefits. And **Conclusion
and Future Work**."

**SIDE:** Eight sections. Name each as you point; don't elaborate yet (~15 s).

---

## Slide 3 — Introduction

**SAY:** "AI now writes about a third of new enterprise code, and **45% of AI-written code ships with
a known security flaw** — Veracode 2025, real codebases. Open-source vulnerabilities per codebase
**jumped 107% in one year** — Black Duck OSSRA 2026. And the tooling to catch this costs
**ten to fifty thousand dollars a year**. So your scanner flags nineteen hundred issues, nobody can
review them all, and **nobody can tell you which one breaches you**. On the right is exactly what a
developer sees, **ninety seconds after they push** — a real bot comment, a real SQL-injection finding,
bad code and the fix, right there."

**SIDE:**
- **What are "Veracode" and "Black Duck"?** Two well-known security companies. Each publishes a yearly
  **research report** analysing millions of real codebases. **Veracode "State of Software Security" 2025**
  is where the **45%** comes from; **Black Duck "OSSRA" 2026** (Open-Source Security & Risk Analysis) is
  where **+107%** comes from. They're your **citations** — you say them so the scary numbers are
  *industry fact, not my opinion.* You don't explain them unless a skeptic asks "where's that from?" →
  then you name the report. That's it.
- *"A third of code"* — GitHub/Microsoft figures on Copilot adoption.
- The screenshot is real output, not a mockup. Point to the HIGH badge, then the fix block.
- **SOURCE:** Veracode 2025 State of Software Security · Black Duck OSSRA 2026.

---

## Slide 4 — Problem Statement (overview)

**SAY:** "Three problems, and they stack. **One — too many alerts, zero trust.** A scan is a wall of
warnings, mostly false; the one real breach hides in the noise. **Two — claimed, never proven.** Tools
say *possible vulnerability* and stop; they never prove it's actually exploitable. **Three — no proof
of provenance.** Results aren't signed, so you can't trust a stranger's pull request, or the code an AI
just wrote into your repo. The common thread: **detection is cheap and noisy — trust is what's missing.**"

**SIDE:**
- **What does "results aren't signed" mean?** *Signed* = a tamper-proof digital **seal** (NOT a name or a
  rule ID). A normal scanner just hands you a list — there's no proof those results came from a real,
  unaltered scan, and no way to prove months later (for an audit) exactly what was found and when.
  Anyone could edit the list. ACR-QA puts a cryptographic seal on every scan (that's Pillar 4) — so it's
  provable and tamper-evident. Plain line: *"You can't trust a result you can't verify."*
- These three problems map one-to-one to the four solution pillars. Plant that now; pay it off on slide 8.

---

## Slide 5 — Problem 1: Too Many Alerts

**SAY:** "Picture the security team's wall: hundreds of warnings, almost all false. One is a real breach.
On the fiftieth pull request of the day, a tired reviewer misses it. **~1,900 raw findings per scan —
which one breaches you?** Volume is not the problem. **Trust is.**"

**SIDE:** ~20 s. Let the image carry it. The number is per-scan on the 30-repo corpus.

---

## Slide 6 — Problem 2: Claimed, Never Proven

**SAY:** "A scanner flags *possible SQL injection* and stops. Is it real? The developer has to guess —
and gets burned either way: ignore a real one, or waste an hour on a false one. **Zero mainstream
scanners actually detonate the bug to prove it.** A claim is not proof."

**SIDE:** ~20 s. This sets up Pillar 3 (Exploit Verification) — foreshadow it.

---

## Slide 7 — Problem 3: No Provenance

**SAY:** "The third problem is **provenance**—which means proof of origin. Imagine you hire a developer to review your codebase, and they hand you a sheet of paper listing 50 security findings. **How do you trust it?** What guarantees they actually ran the tools? What guarantees they didn't delete a few critical findings to hide their own mistakes, or edit the file to add fake findings? Without a cryptographic seal, **nothing is guaranteed**. In modern software supply chains, we are merging code from AI models and strangers' pull requests blindly. Without provenance, **trust is just hope.**"

**SIDE:** ~20 s. This is the EU-CRA / attestation hook (Pillar 4). Note: this is where AI-written code
is a *threat we defend against* — not something we use.

---

## Slide 8 — The Solution: Four Pillars

**SAY:** "ACR-QA is a **trust layer on top of your scanners**. One question at merge time: *is this
finding real enough to stop a release?* Four pillars answer it. **One — deterministic detection:**
thirteen tools across Python, JavaScript, and Go, all collapsed into one schema — **reproducible, the
same code yields the same findings every run.** **Two — trust gates:** reachability, taint, and
confidence scoring cut the noise to **96.4% precision.** **Three — exploit verification:** we detonate
a real payload in a sandbox, then re-detonate the fix. **Four — cryptographic attestation:** every scan
signed with a post-quantum signature. The trust comes from **proof — a detonated exploit and a
signature — not from a model.**"

**SIDE:**
- **This is the identity slide.** The wedge is **proof, not guessing**: exploit verification + signing
  are things an LLM structurally cannot do. Lead there.
- **Go quiet on the LLM.** Don't say "no AI" (you do use one — see Slide 20). Just don't headline it.
- ~50 s — this is the spine of the whole talk.

---

## Slide 9 — Pillar 1: Deterministic Detection

**SAY:** "Detection runs **thirteen tools in parallel** — Ruff, Bandit, Semgrep for Python; ESLint for
JavaScript; staticcheck and gosec for Go. Every tool speaks a different language, so each output
collapses into **one common schema — the CanonicalFinding.** No tool noise crosses that boundary.
The key property: this is **100% rule-based and reproducible.** The same code always yields the same
findings — **no model drift, fully reproducible.** A rule engine, not a black box."

**SIDE:**
- *"One common format"* = `CORE/engines/normalizer.py`. Every downstream engine only sees this schema.
- *"In parallel"* = fast and independent — one tool's false positive can't pollute another's.
- **SOURCE:** `CORE/engines/normalizer.py` · `CORE/detection/tool_runner.py` · `CORE/adapters/`.

---

## Slide 10 — Pillar 2: Trust Gates

**SAY:** "Here's the heart of it — the funnel. On a 30-repo corpus, the tools dump **1,942 raw findings**
— same flood any scanner gives you. Now watch what my trust layer does, in four steps. **First,
confidence scoring** drops the trivial noise — the style nags like *'use const instead of let'* that
no attacker cares about. **Second, reachability** — I check the call graph and ask: *can an attacker
actually reach this code from an entry point?* If the risky function is never called from outside, it
can't be exploited, so I drop it. **Third, taint analysis** — I follow untrusted user input, from the
moment it enters a form, through every variable, until it hits something dangerous like a database
query. If tainted input reaches that query, it's a **real** injection. **Fourth, the Confirmed Tier** —
only findings that are high-severity, on a real security rule, in production code, and high-confidence
survive. **From 1,942 down to 55, at 96.4% precision — safe enough to auto-block a merge.**"

**SIDE (plain-English — this is your explanation, corrected & ready):**
- **Confidence scoring** = rank findings; throw out the trivial style stuff that doesn't matter.
- **Reachability** = *(your version said "unused variables" — that's not it)* — it's: is the vulnerable
  line actually **callable by an attacker** from an entry point? Dead/unreachable code can't be exploited → drop it.
- **Taint** = *(your version was spot-on)* — watch a piece of user input travel from a form/request all
  the way to a dangerous call (SQL, shell, eval). If it arrives unsanitised, the bug is real.
- **Confirmed Tier** = the four-gate final filter: HIGH severity **+** real security rule **+** production
  path (not a test file) **+** high tool-confidence. Pass all four → auto-block. *(That's a good explanation — use it.)*
- **SOURCE:** `CORE/engines/confirmed_tier.py` · `CORE/engines/taint_analyzer.py` · `config/taint_*.yml`.
- **NOTE:** the live demo is **after** the presentation (see the POST-PRESENTATION DEMO section at the very end) — do NOT scan live here, just talk the funnel.

---

## Slide 11 — Pillar 3: Exploit Verification

**SAY:** "This is what makes ACR-QA different. **We don't claim a vulnerability — we detonate it.**
A Docker sandbox spins up, isolated, 128 megabytes, destroyed in 30 seconds, and a real payload fires:
`' OR 1=1`, `{{7×7}}`. Attack confirmed. Then the AI generates a fix, and the **same payload fires
again against the patched code — it must now fail.** If it still works, the fix is wrong. Verified live:
**five out of five** — SQL injection, command injection, template injection, all exploited then blocked.
Static re-analysis can lie. **Re-detonation cannot.**"

**SIDE:**
- All payloads are **safe canary signals** — never destructive. Containers are resource-capped and ephemeral.
- *"Binary ground truth"* = the exploit either fires or it doesn't. No probability, no opinion.
- **SOURCE:** `CORE/engines/` exploit verifier · `TESTS/` exploit suite (5/5, Docker).

---

## Slide 12 — Pillar 4: Cryptographic Attestation

**SAY (plain version — say it like this):** "This brings us to our solution for provenance. Remember that sheet of paper with 50 findings? With ACR-QA, that paper is now **sealed in two ways and cryptographically fingerprinted in a chain**. We apply two signatures: **ECDSA**, which secures modern mobile banking, and **Dilithium**, a post-quantum standard that secures findings against future quantum computers. Every detail—the scan time, the tool versions, the code, and each finding—is fingerprinted and bound together. If a developer edits even a single letter in the database or the report, the seal instantly breaks. You don't have to trust the developer, and you don't have to trust me—**you trust the mathematics of the seal.**"

**SIDE — plain-English cheat sheet (so YOU understand every word):**
- **"Signed"** = a *digital signature* — a tamper-proof seal. It does **two** things: proves it's genuine,
  and breaks if anyone alters even one character. *(It is NOT a name or a rule ID like SECURITY-001.)*
- **ECDSA-P256** = "the normal signature the whole internet already uses" — the padlock in your browser,
  online banking. P256 is just its strength. Nothing exotic.
- **Dilithium3** = "the quantum-safe signature." Today's signatures could one day be broken by a quantum
  computer; this one can't. It's NIST-standardised (FIPS 204). If asked the math → *"it's lattice-based —
  the property is what matters, not the proof."* Say the name and move on.
- **"Hashed into a Merkle chain"** = a *hash* is a digital **fingerprint** of data — change one letter and
  the fingerprint changes completely. Chaining all the pieces' fingerprints means tampering **anywhere**
  breaks the chain. Like a tamper-evident chain-of-custody for evidence.
- **Provenance** = "proof of origin" — what was scanned, when, with which tool versions.
- **If you remember ONE sentence:** *"I put a tamper-proof, quantum-safe seal on every scan, so anyone can
  verify later that the result is real and unchanged."*
- This is the answer to Problem 3 ("results aren't signed") — tie them together out loud.
- **SOURCE:** `CORE/engines/attestation.py` · dashboard Attestation view.

---

## Slide 13 — System Architecture

**SAY:** "Here's the whole system, five layers. **Clients** — GitHub, CI/CD, the dashboard, the CLI —
hit a **52-endpoint FastAPI service** with JWT auth. **Celery** picks up the job on a Redis queue,
four workers. The **analysis pipeline** runs the four pillars I just showed. Results land in
**PostgreSQL**, metrics in **Prometheus and Grafana.** The numbers on the right: **96.4% precision,
100% CVE recall, F-one of 98.2% versus Semgrep's 45.7%, 3,247 tests at 88% coverage.** And the line at
the bottom is the one to remember: **the proof — exploit verification and signing — is deterministic.
An LLM cannot detonate a bug or sign a result.**"

**SIDE:**
- Walk the diagram top-to-bottom: Clients → API → Workers → Pipeline → Storage. The arrows show the data.
- The right column is your number bank — point, don't read all four.
- **SOURCE:** `CORE/main.py` · `FRONTEND/api/` · `DATABASE/database.py`.

---

## Slide 14 — Evaluation Methodology

**SAY:** "How do I know the numbers are honest? Four principles. **One — no training set:** this isn't
machine learning, it's deterministic rules, so there's nothing to overfit or cherry-pick. **Two —
pre-registered:** I declared the CVE battery *before* I tested, so I couldn't tune to it — and got 100%
recall on it. **Three — third-party ground truth:** RealVuln's labels are external, published, not
graded by me. **Four — manual triage:** every Confirmed-Tier finding was hand-verified to earn the
96.4% precision. Tested across RealVuln, OWASP, SecurityEval, a 30-repo adversarial corpus, and the
CVE battery."

**SIDE:**
- This slide answers the committee's *"how did you validate?"* — lead with **pre-registered** and
  **third-party ground truth**; those are the two that kill "you graded your own homework."
- *"No training set"* = not ML, nothing to overfit. *"Pre-registered"* = wrote down the test before running it.
- **SOURCE:** `TESTS/evaluation/` · `docs/evaluation/` benchmark docs · RealVuln arXiv:2604.13764.

---

## Slide 15 — Results: Why Trust Gates Exist (the confusion matrix)

**SAY:** "This is the honest picture, and it's the strongest argument I have. On SecurityEval, **raw
detection catches almost everything — 91% recall.** But look at the false alarms: **raw precision is
only 54.7%** — sixty-seven false positives. *That gap* is the problem. And here's the fix: the
**Confirmed Tier collapses those false alarms and lifts precision to 96.4%.** Honest raw number, strong
final one — same scan, two operating points: recall-first for triage, precision-first for auto-block."

**SIDE:**
- Don't hide the 54.7%. **Owning it is what makes the 96.4% credible.** A committee trusts honesty.
- The 67 false positives are SecurityEval's *adversarially-designed* clean snippets — not real-codebase noise.
  If they fixate on the high FPR, it's a corpus artefact of 89 tiny clean files; precision is the size-immune number.
- **SOURCE:** `ACR-QA-Book/figures/CONFUSION_MATRIX_SLIDE.png` · SecurityEval (89+89, CWE-matched). Counts: TP=81, FN=8, FP=67, TN=22.

---

## Slide 16 — Results: Across Five Benchmarks (scorecard)

**SAY:** "And it's not one test — it's five, each measuring a different thing. **CVE battery: a hundred
percent recall. Head-to-head F-one: ninety-eight. Confirmed-Tier precision: ninety-six. SecurityEval
recall: ninety-one. OWASP Top-Ten: nine of ten categories.** Five different metrics, all between ninety
and a hundred percent. This isn't cherry-picking one friendly benchmark — it's strong across the board.
The one genuinely hard number, real-world recall, is the next slide — and even there we're number one."

**SIDE:**
- Each bar is labelled with its metric type (precision / recall / F₁ / coverage) — say so, so no one
  thinks you're mixing metrics dishonestly.
- This slide exists to answer "are you just good at one easy test?" — no, five different ones.
- **SOURCE:** `scripts/build_eval_figures.py` · all numbers documented in `docs/QA_PREP.md` evidence table.

---

## Slide 17 — Results: #1 Against Every Competitor

**SAY:** "Now the hardest test — real-world CVEs from real apps, third-party ground truth. The absolute
numbers are low for *everyone*, because much of real-world vulnerability needs runtime state no static
tool can see. But look at the ranking: **ACR-QA at 25.1% leads Bandit, Semgrep, Snyk, and SonarQube.**
And on the head-to-head, **F-one of 98.2% versus Semgrep's 45.7%.** Public benchmarks, reproducible —
on the hardest real-world test, we're number one."

**SIDE:**
- **Lead with the ranking, not the 25%.** "#1 of five" is the message; the absolute number is hard for everyone.
- If asked why so low: many real CVEs are auth/IDOR/business-logic — undecidable for static analysis (Rice's theorem).
- *(The live demo comes after you finish the slides — see POST-PRESENTATION DEMO at the end.)*

---

## Slide 18 — Use Cases

**SAY:** "One trust layer, four people who can't afford to guess wrong. **The university instructor** —
free, self-hosted, the real bug surfaced, the explanation teaches. **The startup lead** — a 96.4%
auto-block that won't cry wolf, plus a signed audit trail for EU CRA. **The open-source maintainer** —
trust the code, not the contributor. **The enterprise auditor** — every scan signed, verifiable in one
command, months later."

**SIDE:** ~30 s. Four quadrants — one line each, don't dwell.

---

## Slide 19 — Conclusion & Future Work

**SAY:** "ACR-QA fills the quadrant the market leaves empty: **open, attested, zero-dollar.** **Trust** —
96.4% precision, auto-block grade. **Proof** — exploit-verified and signed, not guesses. **Reach** —
13 tools, three languages, 100% CVE recall. **Price** — $0 recurring versus $10–50k a year. The
honest gaps: **inter-procedural taint** for more recall, **more languages**, a **hosted GitHub App**,
and **independent expert labelling.** But the core is done — this is **not a proposal, it is a running
system.**"

**SIDE:**
- The quadrant image = three locked doors, one open. That's the gap. Land "running system" slowly.
- Naming the gaps yourself disarms the committee — they can't "catch" what you've already raised.

---

## Slide 20 — Any Questions?

**SAY:** "Thank you — I'm happy to go deeper on any number or any slide."

**Rapid-fire Q&A prep:**
- **"Do you use any AI / is this an AI wrapper?"** *(the honest answer — never deny it)* → "I do use an
  LLM, but only as an **optional second opinion** — it flags code my deterministic tools might have
  missed, and it adds about five to seven points of recall. The key is it **never gets the final word**:
  it's gated by a confidence threshold, and anything it raises still has to pass the same exploit
  verification. The trust never depends on the model — it depends on a **detonated exploit and a
  signature**, and *that* is something no LLM can do. So no, it's the opposite of a wrapper: the AI is a
  small helper bolted onto a deterministic proof engine."
- **"Why not just collect a dataset and train a machine-learning model?"** → "Three reasons. One — there
  is no honest labelled dataset big enough; security ground truth is scarce and expensive, which is
  exactly why I hand-label. Two — an ML model would be the **non-reproducible, hallucinating** thing I'm
  trying to beat: it can't explain *why*, and it drifts. Three — and decisively — **a model still can't
  prove a bug is exploitable or sign the result.** My contribution is verification and provenance, not
  classification. Detection is the easy part; **trust** is the thesis."
- **"Why test on only 30 repos, not 100?"** → "Three reasons. One — they're an *adversarial* corpus,
  hand-built to be noisy and hard; 30 nasty repos stress precision more than 100 easy ones. Two — every
  finding is *manually ground-truthed*; quality of labels beats quantity, and labelling 100 by hand
  solo wasn't feasible. Three — the 95% confidence interval (90.9–100%) already shows the number is
  stable, so more repos wouldn't move it much. Recall is measured *separately* on RealVuln's 26 real
  CVE apps and a pre-registered 8-CVE battery. Scaling to a 100-repo multi-annotator study is named
  future work."
- **"Why is raw precision only 54.7%?"** → "Adversarial clean snippets, by design. The Confirmed Tier
  lifts it to 96.4% — that's the whole contribution."
- **"How is 96.4% verified?"** → "30-repo corpus, Confirmed-Tier filter, 95% CI 90.9–100%. `confirmed_tier.py`."
- **"What if the exploit harness has a bug?"** → "Binary and reproducible — 5/5 live, payloads are safe canaries."
- **"Recall vs commercial tools?"** → "RealVuln 25.1%, leading Semgrep/Snyk/SonarQube; 100% on the pre-registered CVE battery."
- **"You said 91% recall on slide 15, then 25% on slide 17 — which is it?"** ⚠️ likely question → "Two
  different tests. 91% is on **SecurityEval** — tiny isolated code snippets, one bug each; it proves my
  detection *algorithm* is sound. 25% is on **RealVuln** — real, full applications, which are genuinely
  hard for *every* tool because many real bugs need runtime context no static analyser can see. The number
  that matters on RealVuln isn't the 25 — it's that I **rank #1**, ahead of Semgrep, Snyk, and SonarQube.
  I report both honestly because each measures something different. Analogy: a spelling test vs proofreading
  a whole novel."
- **"Post-quantum — is that real or buzz?"** → "Dilithium3, NIST FIPS 204, 2024. Required reading for EU CRA Sept 2026."
- **"In simple terms, what is Dilithium / your signature?"** → "A digital signature is like a tamper-proof
  wax seal on the scan — if anyone changes one finding, the seal breaks. I use two seals: ECDSA, the
  normal one banks and HTTPS use; and Dilithium, a newer one that even a future quantum computer can't
  forge. I don't need the math — I just need to say it survives quantum attacks, which is what the EU's
  2026 Cyber Resilience Act will require." *(If pushed on math: "it's lattice-based — but the point is the property, not the proof.")*
- **"Which OWASP Top-10 category do you NOT cover, and why?"** → "**A09 — Security Logging & Monitoring
  Failures.** It's the one category that isn't a code pattern — it's about whether the running app *logs*
  security events and *monitors* them in production. Static analysis reads code; it can't judge whether
  logging is adequate at runtime. So I honestly report 9 of 10 — and A09 is architecturally out of scope
  for *any* static tool, not just mine."

---

## Slide 21 — Thank You

**SAY:** "Thank you. **Ahmed Mahmoud Abbas**, supervised by **Dr. Samy Abdel Nabi.** I'd be glad to show
the system running, if you'd like."

**SIDE:** Smile, hold, invite questions. If they say yes to a demo → go to POST-PRESENTATION DEMO below.

---

# ▶ POST-PRESENTATION DEMO — 5 minutes, minute-by-minute (run AFTER the slides, 100% GUI, no terminal)

**SETUP (the night before — terminal used ONCE, in private):**
1. `make seed-demo` → seeds the dashboard with **payments-api, 64 findings, Confirmed Tier, attestation** (real, reproducible).
2. Start the API: `uvicorn FRONTEND.api.main:app --port 8000`. Start the dashboard: `cd dashboard && npm run dev`.
3. **Open the browser and LOG IN before you walk in** — the committee never sees the login page, just the dashboard.
4. Confirm **internet works** in the room. **Pre-test the dvpwa scan once** so you know it works that day.
5. Click through the funnel once and **write down the REAL numbers** (exact Confirmed-Tier count, which finding is the SQLi).

**THE KEY TRICK: start the live scan FIRST so its ~1-min wait runs in the background while you talk.**

| Time | What you click | What you SAY |
|------|----------------|--------------|
| **0:00–0:20** | **New Scan → paste `https://github.com/anxolerd/dvpwa` → Scan.** Leave it running, switch tabs. | *"I'm pointing it at a GitHub repo it's never seen — live. While it clones and scans, let me show you a scan I ran earlier."* |
| **0:20–2:00** | **Overview** → open **payments-api** run → **toggle Confirmed Tier** → click the top **HIGH** finding. | *"Live dashboard, real data. One scan — 64 findings, the flood any scanner gives you. Now watch — 64 down to 4. Only these four are safe enough to auto-block a merge. Here's one: exact file, line, the rule, a plain-English explanation."* *(say the real Confirmed-Tier number)* |
| **2:00–3:00** | Open the **Attestation** view. | *"The whole scan is cryptographically sealed — tamper-proof and quantum-safe. Change one finding, the seal breaks. Anyone can verify it later."* |
| **3:00–4:00** | **Runs/Fleet** list — point at one repo per language. | *"And it's not just Python — here's JavaScript (juiceshop), and Go (go-vuln-demo). Same trust layer, three languages."* |
| **4:00–4:45** | Switch back to the **live scan tab** (now finished). Toggle Confirmed Tier. | *"And here's the live one — done. 32 findings on a repo it had never seen, already signed."* |
| **4:45–5:00** | — | *"Raw findings in, trusted findings out, cryptographically signed — live, in front of you. That's ACR-QA."* |

**🛟 IF THE SCAN FAILS / no internet:** skip 4:00–4:45 entirely. Spend the time on the funnel + 3 languages —
the demo is **complete without the live scan**. *"I'll show the run I did this morning."* Never wait on a broken scan, never debug live.

**Notes:** payments-api's exploit tier is mostly 'unverified' — don't claim a live detonation in the demo
(that story is Slide 11). ❌ Never use the **"Full" local-folder** scan live (slow: minutes). The GitHub-URL scan is the only live path. No manual refresh anywhere — results auto-appear.
