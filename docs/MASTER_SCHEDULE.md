# Master Schedule — Thesis Defense Runway

**Status:** Active · **Defense runway:** 4+ weeks (~May 17 — June 14, 2026)
**Target tag:** v4.6.0 (UI Phase 3 + Eval Bulletproofing + Distribution)
**Single source of truth for sequencing across all 5 plans.**

---

## Why this doc exists

Five plan MDs (UI Phase 3, UI Testing, Eval Bulletproofing, Distribution, plus the existing PRESENTATION_SCRIPT) each describe what to build. This doc says **when** and **in what order**. It exists because:

- Without a master schedule, plans get executed in random order and dependencies break
- Critical-path work (CVE pilot) gets buried by lower-priority work (glassmorphism polish)
- A 4-week runway is plenty, but only if we don't waste it building things in the wrong order

## Sequencing Principle

**Risk-first, then ship, then polish:**

1. **Risk-first** — Tier 0 + CVE pilot in W1. If CVE recall disappoints, we have 3 weeks to pivot defense narrative.
2. **Ship** — Lock in eval numbers (W2) before UI (W3–W4). Better to have boring UI + strong eval than beautiful UI + weak eval.
3. **Polish** — Demo video and final commits in W5.

## The 5-Week Plan

### Week 1 (~10h) — Risk-First Eval
| Day | Task | Hours | Source plan |
|-----|------|------:|-------------|
| Mon | Tier 0 integrity infrastructure | 3 | EVAL_BULLETPROOFING |
| Mon | CVE pilot — 5 CVEs only | 2 | EVAL_BULLETPROOFING (Tier 1) |
| Tue | **Decision gate:** review pilot results | 0.5 | — |
| Tue–Fri | Start Tier 1 full (~5h of 15h) | 5 | EVAL_BULLETPROOFING (Tier 1) |

**Decision gate criteria:**
- Pilot recall > 60% → commit to full Tier 1
- Pilot recall 30–60% → continue Tier 1 but lead defense with FP rate
- Pilot recall < 30% → pivot: skip full CVE table, lean entirely on FP rate + corpus diversity

### Week 2 (~12h) — Lock In Eval Numbers
| Task | Hours | Source plan |
|------|------:|-------------|
| Finish Tier 1 CVE recall (full 15–20 CVEs) | 10 | EVAL_BULLETPROOFING (Tier 1) |
| Start Tier 3 corpus expansion (govwa + 1 repo) | 2 | EVAL_BULLETPROOFING (Tier 3) |

### Week 3 (~12h) — Finish Eval, Start UI
| Task | Hours | Source plan |
|------|------:|-------------|
| Finish Tier 3 corpus expansion (Django + FastAPI + TS) | 6 | EVAL_BULLETPROOFING (Tier 3) |
| UI Phase 1: landing + auth UX (signup/verify/forgot/login) | 6 | UI_PHASE_3 |

### Week 4 (~14h) — Polish + Independent Validation
| Task | Hours | Source plan |
|------|------:|-------------|
| UI Phase 2: killer finding detail page | 4 | UI_PHASE_3 |
| UI Phase 3: demo mode (`?demo=1`) | 1 | UI_PHASE_3 |
| UI Phase 4: smart polish | 1 | UI_PHASE_3 |
| UI testing: 5 unit + 5 E2E + 5 a11y + manual checklist | 3 | UI_TESTING |
| Tier 2 peer validation (κ on 20-finding sample) | 3 | EVAL_BULLETPROOFING (Tier 2) |
| Update EVALUATION.md with final numbers | 2 | EVAL_BULLETPROOFING |

### Week 5 (~11h) — Distribution + Demo Video
| Task | Hours | Source plan |
|------|------:|-------------|
| PyPI release (`pip install acrqa`) | 4 | DISTRIBUTION |
| GitHub Actions Marketplace listing | 3 | DISTRIBUTION |
| Demo video filming (5 min, OBS) | 3 | task 12.35 |
| YouTube upload + final commits | 1 | task 12.36 |

---

## Totals

| | Hours |
|---|------:|
| Eval Bulletproofing (Tiers 0–3) | 29 |
| UI Phase 3 (all 4 sub-phases) | 12 |
| UI Testing | 3 |
| Distribution (PyPI + Marketplace) | 7 |
| Demo video + YouTube | 4 |
| **Grand total** | **~55** |

Spread over 5 weeks = ~11h/week. Realistic.

---

## Cuts From Original Plans (To Avoid Scope Creep)

| Cut | Why |
|-----|-----|
| Multi-step scan wizard | Current single-page works |
| Glassmorphism polish | Cosmetic, low defendable claim |
| Marimo notebook updates | Already linked, low marginal value |
| Standalone OWASP heatmap page | Existing endpoint is enough |
| Knowledge base browser page | Nobody browses 66 rules |
| CBoM standalone page | 3 users care |
| Test Gap Analyzer page | CLI is fine |
| Documentation viewer in UI | Overengineering |

## Plan Document Map

| Plan | What it covers | Weeks |
|------|----------------|------:|
| `EVAL_EXPANSION_PLAN.md` | Tier 0 integrity + Tier 1 CVE recall + Tier 2 peer κ + Tier 3 corpus | W1–W4 |
| `UI_PHASE_3_PLAN.md` | Landing + auth UX + killer finding detail + demo mode + polish | W3–W4 |
| `UI_TESTING_PLAN.md` | 15 automated tests + 20-item manual checklist | W4 |
| `DISTRIBUTION_PLAN.md` | PyPI release + GitHub Actions Marketplace listing | W5 |
| `evaluation/INTEGRITY.md` | Charter for evaluation honesty (Tier 0 deliverable) | W1 |
| `PRESENTATION_SCRIPT.md` | Verbal defense + Q&A cheat sheet | Updated W4 |
| `DEMO_VIDEO_SCRIPT.md` | 5-minute filming script (task 12.35) | W5 |

---

## Risk Register

| Risk | Probability | Mitigation |
|------|:-----------:|------------|
| CVE pilot shows weak recall (<30%) | Medium | Decision gate at end of W1; pivot to FP-rate-led defense |
| Peer reviewers unavailable | Medium | Fallback to 1 reviewer + author, document as limitation |
| Demo video filming takes multiple takes | Medium | Budget 6h for filming if 3h insufficient |
| Real production bugs surface during eval | Low | Treat as win — bugs found in eval are bugs fixed in product |
| Scope creep adds new "must-haves" | High | This doc is the contract — defer all additions to post-defense |
| Defense moves earlier than expected | Low | Tier 0 + Tier 1 + Week 5 (demo video) is the minimum shippable; everything else defers |

## Weekly Check-in Format

End of each week, update this doc with:
- ✅ What got done
- ⚠️ What slipped and why
- 🔄 What changed in next week's plan as a result

This is the lived-in version of the plan, not the aspirational one.

---

## Success Criteria (End of W5)

- [ ] Tier 0 integrity infrastructure in place; `make eval-reproduce` works
- [ ] Tier 1 CVE recall table published in `docs/evaluation/CVE_RECALL.md`
- [ ] Tier 2 peer validation κ documented in `docs/evaluation/PEER_VALIDATION.md`
- [ ] Tier 3 corpus expanded to 16 repos across 4 languages
- [ ] UI Phase 3 shipped (landing + auth UX + killer finding detail + demo mode)
- [ ] UI Testing all green (5 unit + 5 E2E + 5 a11y pass; manual checklist 20/20)
- [ ] PyPI package live, downloadable via `pip install acrqa`
- [ ] GitHub Actions Marketplace listing live
- [ ] Demo video uploaded to YouTube
- [ ] v4.6.0 tagged and pushed
- [ ] PRESENTATION_SCRIPT.md verbal pivots updated with new numbers
