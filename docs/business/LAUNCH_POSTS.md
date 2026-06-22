# ACR-QA Launch Posts

> **Status (2026-06-21):** Defense DONE. Open-source launch pending.
> Post HN + LinkedIn same day. Blog post optional follow-up.
> See `VIDEO_SCRIPT.md` for the 75-second marketing video.

---

## LinkedIn Post — GOD MODE (SWE/Backend job target)

> **Goal:** attract recruiters + developers. Engineering breadth is the flex, not "security product."
> **CTA:** backend / devops / any SWE job (primary) + soft OSS mention (secondary).
> **Hashtags:** 3-5 max — LinkedIn uses them as category signals, not discovery feeds.
> **Links:** NO link in post or comments — LinkedIn penalises "bridge behaviour" at ~60% reach loss.
>   GitHub goes in your profile's Featured section. Video IS the demo.

```
I solo-built a full-stack system from scratch for my graduation thesis.
In 9 months.

Here's what's inside:

→ FastAPI backend · 36 engine modules · 13 detection tools
→ React 18 dashboard (TypeScript, Tailwind, SSE live progress)
→ PostgreSQL + Redis + Docker Compose + Kubernetes operator
→ CI/CD pipeline with GitHub Actions, pre-commit hooks, SLSA L3 provenance
→ 3,247 tests · 88% CORE coverage

The domain is security — it's a static analysis tool that verifies bugs
live in a Docker sandbox and signs every finding with ECDSA attestation.

But what I'm proud of is building ALL of it alone. End to end.

My supervisor, Dr. Samy AbdelNabi, told me it was
"too ambitious for a graduation project."

I shipped it anyway.

The numbers held up in committee:
96.4% precision. 8/8 CVEs caught. Outperforms Semgrep and Snyk
on a real-world vulnerability benchmark.

Now I'm looking for my first role — backend, devops, or any SWE position.
Open to relocation. Open to remote.

If you're hiring or know someone who is — my DMs are open.

#opentowork #softwareengineering #backend #devops #hiring
```

> **Note on posting:** attach the demo video directly to this post (native upload).
> No external links in the post or first comment — LinkedIn's 2026 algorithm
> penalises both. GitHub link goes in your profile's Featured section only.

---

## Hacker News — "Show HN"

**Title:** (pick one — the second leads with the 2026-relevant LLM-scanner angle)
```
Show HN: ACR-QA – open-source SAST that reaches 96.4% precision on production code (F1=98.2%)
```
```
Show HN: A deterministic SAST that matches frontier-LLM recall at $0 — and gives the same answer every run
```
> The second title is the stronger 2026 hook: LLM security scanners are everywhere now, and the
> reproducibility argument (a clean LLM scan ≠ clean code, because the next run finds *different*
> bugs) is a debate HN will engage with. Be precise in the body: the top LLMs out-recall ACR-QA per
> scan; ACR-QA's edge is determinism/$0, not "more bugs." Do not claim it finds more — HN will check.

**Body:**
```
I built ACR-QA as my CS graduation thesis at KSIU. It orchestrates 13 detection tools
(Bandit, Semgrep, Ruff, gosec, ESLint, Trivy, Trufflehog, staticcheck, vulture, radon,
jscpd, secrets-detector, OSV-SCA), normalises everything into one schema across 36 engine
modules, and uses RAG-grounded Groq LLaMA to explain each finding.

The problem: most SAST tools have 8–30% precision in practice — developers learn to ignore them.

My approach: a 4-criterion "Confirmed Tier" filter (HIGH severity + 22-rule confirmed set +
production code path + Bandit internal HIGH confidence) that reaches 96.4% precision
(95% CI [90.9%, 100%]) while preserving 100% CVE recall.

Head-to-head on the same 30-repo adversarial corpus (top-20 PyPI + top-6 npm + top-4 Go):
  Bandit alone:     F1 = 21.8%  (1/8 CVEs caught)
  Semgrep CE alone: F1 = 45.7%  (5/8 CVEs caught)
  ACR-QA P4:        F1 = 98.2%  (8/8 CVEs caught)

RealVuln benchmark (22 real-world vulnerable repos, official scorer, same repo set for all):
  SonarQube: 5.2% recall
  Snyk:      14.9% recall
  Semgrep:   17.6% recall
  ACR-QA:    50.0% recall  (zero-LLM, deterministic, $0)
On 16 repos the engine was NEVER tuned on, it still gets 46% recall vs Semgrep's 18%.

vs frontier-LLM agentic scanners (GPT-5.5, Claude Opus 4.8, Gemini, etc.): ACR-QA's recall sits in
the frontier range — it ties Claude Opus 4.8 and Gemini, beats Grok/Qwen, at $0 and deterministic.
The strongest LLMs (GPT-5.5 ~57%) out-recall it per scan, and LLMs win on precision (80%+ vs ~49%,
via exploitability reasoning). What ACR-QA has that they don't: it returns the SAME findings every
run. Those agents are non-deterministic — across 3 runs only ~71% of their findings are stable
(Grok: 48%), they cost up to $62/benchmark, and a clean scan doesn't mean clean code because the
next run finds different bugs. For reproducible CI gates, scan diffing, and auditability, that
determinism is the differentiator — not a higher bug count.

Exploit verification: each HIGH finding is detonated live in a Docker sandbox to confirm
exploitability before surfacing to the developer.

Attestation: ECDSA-P256 signature + Dilithium3 post-quantum signature + Sigstore Rekor
transparency log entry per scan.

One-liner to try it:
  docker run --rm -v $(pwd):/scan -e GROQ_API_KEY_1=your_key \
    ghcr.io/ahmed-145/acrqa:latest \
    python3 CORE/main.py --target-dir /scan --rich

What's in the box:
  - FastAPI service + React 18 dashboard (WCAG 2.1 AA, Arabic RTL)
  - Differential SAST (new-only findings vs last scan)
  - RAG-grounded AI explanations via Groq LLaMA
  - ECDSA + Dilithium3 attestation per scan
  - 3,247 tests, 88% CORE coverage
  - $0 recurring cost to run

GitHub: https://github.com/ahmed-145/ACR-QA

Happy to answer questions about the evaluation methodology, the Confirmed Tier design,
or why I chose this over just running Bandit + Semgrep together.
```

---

## Blog Post Outline

**Platform options (all free):** dev.to · hashnode.dev · medium.com

**Title:** "How I Got 96.4% SAST Precision: The Confirmed Tier Explained"

**Sections:**
1. The problem: false positive fatigue in static analysis
2. Architecture overview (pipeline diagram — use `arch_system_slide.png`)
3. The 4-criterion Confirmed Tier gate (1,942 raw → 55 confirmed)
4. Head-to-head results: Bandit vs Semgrep CE vs ACR-QA P4
5. RealVuln benchmark: how it beats Semgrep and Snyk on real repos
6. Exploit verification: why "detonating" findings matters
7. Attestation: ECDSA + post-quantum + Sigstore
8. What I'd do differently (inter-procedural taint, more language coverage)
9. How to run it yourself (Docker one-liner)

**Target length:** 1,200–1,800 words
**Publish:** same day as HN post
