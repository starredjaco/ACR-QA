# ACR-QA Dashboard — God Mode Plan

> Say **"go god mode phase N"** to execute any phase.
> Last updated: **2026-05-22**

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ | Shipped |
| 🚧 | In progress |
| 📋 | Planned, not started |
| 🧊 | Deferred, deliberately |
| ❌ | Cut |

---

## Shipped Baseline

All UI-UX Pro Max work (A1–A6 + P1–P5) is done. These are the foundation every phase below builds on.

| # | Item | Status |
|---|---|---|
| A1 | Foundation component kit: `Sparkline`, `CountUp`, `SkeletonRow`, `SidePanel`, `EmptyState`, `StatusBar`, `KbdHint`, `Tooltip`, `OWASPDonut`, `TopRulesBar` | ✅ |
| A2 | Lib utilities: `useUrlState`, `useDensity`, `useShortcuts`, `demoData` | ✅ |
| A3 | `/overview` bento dashboard with dot-grid HUD background | ✅ |
| A4 | `/findings` URL-state filters, j/k navigation, side panel, severity tinting | ✅ |
| A5 | `/analytics` upgraded with recharts (Trend, Treemap, Radar, Calendar) | ✅ |
| A6 | StatusBar (density toggle), Command palette, toast Zustand store | ✅ |
| P1 | HUD/FUI: corner brackets, glow pulse, scan-line shimmer, `prefers-reduced-motion`, `ThreatLevel` pill | ✅ |
| P2 | `AlertBanner`, `ShortcutsModal` (`?` shortcut), live HIGH count in sidebar | ✅ |
| P3 | Recharts components: `FindingsTrendChart`, `OWASPTreemap`, `CategoryRadar`, `ScanCalendar` | ✅ |
| P4 | Route-level `React.lazy()` code splitting; `content-visibility` on table rows | ✅ |
| P5 | `FindingModal` HUD card, `evidence-block` syntax styling, gradient confidence bar | ✅ |

---

## The Architecture Reframe

The dashboard today is shaped around **runs**. Mature security platforms (Sentry, Linear, Snyk, GitHub Advanced Security) are shaped around **persistent objects with state, relationships, and workflows**. The phases below execute that shift.

Three architectural shifts underpin all phases:

- **Shift 1 — Findings → Vulnerabilities**: A `Vulnerability` is a persistent first-class object. A `Finding` is a detection event that attaches to it.
- **Shift 2 — Pages → Operations**: Router collapses from 16 routes to 5 surfaces. Navigation is by workflow, not by noun.
- **Shift 3 — Objects → Relationships**: Every object has a navigable graph of neighbours. One click to anything related.

---

## Phase 0 — Vulnerability Schema & Identity ✅

**Execute with:** `go god mode phase 0`

**Goal:** The migration. Nothing else gets built until findings have persistent identity.

| Task | Detail | Status |
|---|---|---|
| 0.1 | `vulnerabilities` table: `id`, `fingerprint`, `short_id`, `canonical_rule_id`, `file_path`, `status` (enum), `owner`, `severity`, `first_seen_at`, `last_seen_at`, `resolved_at`, `created_at`, `updated_at` | ✅ |
| 0.2 | Fingerprint: `SHA256(canonical_rule_id "::" file_path "::" normalized_snippet)` — leading/trailing + multi-space whitespace collapsed | ✅ |
| 0.3 | Alembic migration `0019` — `vulnerabilities` table + `vulnerability_id FK` on `findings` | ✅ |
| 0.4 | `scripts/backfill_vulns.py` — one-shot re-fingerprint all existing findings | ✅ |
| 0.5 | `/v1/vulnerabilities` — list, get by id, get by short_id, PATCH status, PATCH owner, GET findings | ✅ |
| 0.6 | Lifecycle: `detected → confirmed → assigned → in_progress → fixed → verified → regressed` + `dismissed` | ✅ |
| 0.7 | `insert_finding` auto-fingerprints + links every new finding to a Vulnerability on creation | ✅ |

**Files shipped:**
- `CORE/engines/fingerprint.py`
- `alembic/versions/20260522_0019_vulnerabilities.py`
- `DATABASE/database.py` — 8 new methods
- `FRONTEND/api/routers/vulnerabilities.py`
- `FRONTEND/api/main.py` — router wired
- `scripts/backfill_vulns.py`

**To activate:**
```bash
alembic upgrade head
python scripts/backfill_vulns.py
```

**Unblocks:** Every other phase.

---

## Phase 1 — Vuln Detail Page ✅

**Execute with:** `go god mode phase 1`

**Goal:** The canonical page. Every link in the platform points here. Build it well — everything inherits its quality.

**Depends on:** Phase 0

| Task | Detail | Status |
|---|---|---|
| 1.1 | Route `/vuln/:shortId` — long scroll, sticky left section nav (192px), IntersectionObserver active-section tracking | ✅ |
| 1.2 | Header: severity pill, rule ID, file path, lifecycle status dropdown, owner inline-edit, age, detection count, confidence bar | ✅ |
| 1.3 | Timeline section: detection events + triage verdicts + ensemble reviews, chronological with colour-coded dots | ✅ |
| 1.4 | Code context section: evidence snippet + taint source display | ✅ |
| 1.5 | Ensemble panel: primary/secondary verdict cards, agreement banner | ✅ |
| 1.6 | Related vulns: same canonical_rule_id, excludes self, links to each vuln's detail page | ✅ |
| 1.7 | Fix section: autofix patch diff + validation note + link to full run | ✅ |
| 1.8 | Attestation section: ECDSA key_id + algorithms display | ✅ |
| 1.9 | CVE/CWE reference cards: static mapping for known rules + Search CWE / NVD fallback | ✅ |
| 1.10 | `@media print`: hides sidebar/nav/topbar, forces black-on-white, expands all sections | ✅ |

**Files shipped:**
- `src/routes/vuln.$shortId.tsx` — 18.5 KB lazy chunk
- `src/lib/api.ts` — `Vulnerability`, `VulnFindingEvent`, `VulnFindingsResponse` types + 5 API functions
- `src/lib/queries.ts` — `useVulnerability`, `useVulnFindings`, `useVulnerabilities`, `usePatchVulnStatus`, `usePatchVulnOwner`
- `src/styles/acr.css` — `.vuln-layout`, `.vuln-section-nav`, `.vuln-status.*`, `.timeline*`, `.ensemble-*`, `.related-*`, `.ref-card*`, `@media print`
- `src/App.tsx` — route `/vuln/:shortId` wired
- `src/routes/_layout.tsx` — "Vulnerabilities" nav item added

---

## Phase 2 — Inbox ✅

**Execute with:** `go god mode phase 2`

**Goal:** Replace `/overview` as the default landing. The notification center, triage queue, and Discover operation all live here.

**Depends on:** Phase 0, Phase 1

| Task | Detail | Status |
|---|---|---|
| 2.1 | Route `/inbox` + `HomeRedirect` updated — authenticated users land on Inbox by default | ✅ |
| 2.2 | Six feed sections: Regressions → Stale TPs → Disagreements → New vulns → Assigned to me → PR vulns. Grouped view when lens = "all", flat view per lens tab | ✅ |
| 2.3 | Keyboard: `j`/`k` navigate, `t` confirm TP, `f` dismiss FP, `a` assign modal, `e`/`Enter` open vuln detail | ✅ |
| 2.4 | Bulk select: `x` toggles item, bulk action bar with Confirm / Dismiss / Assign / Clear; `POST /v1/inbox/bulk` | ✅ |
| 2.5 | PR Risk lens tab wired — `pr_risk.py` validated (all 13 tests pass) | ✅ |
| 2.6 | "All caught up" empty state with ✓ icon and link to findings | ✅ |
| 2.7 | Desktop `Notification` API on regression count increase; 60s auto-refresh via `refetchInterval` | ✅ |

**Files shipped:**
- `src/routes/inbox.tsx` — Inbox page
- `src/lib/api.ts` — `InboxResponse` type + `getInbox`, `bulkPatch`
- `src/lib/queries.ts` — `useInbox`, `useBulkPatch`
- `src/styles/acr.css` — `.inbox-*`, `.bulk-bar`, `.inbox-empty` classes
- `src/App.tsx` — `/inbox` route + HomeRedirect → `/inbox`
- `src/routes/_layout.tsx` — Inbox nav item with live count badge
- `DATABASE/database.py` — `get_inbox()` with 6 pre-categorised SQL queries
- `FRONTEND/api/routers/inbox.py` — `GET /v1/inbox`, `POST /v1/inbox/bulk`
- `FRONTEND/api/main.py` — inbox router wired
- **Bugfix:** `from datetime import UTC` → `timezone.utc` in `database.py` + `backfill_vulns.py` (Python 3.10 compat)

---

## Phase 3 — Relationship Layer ✅

**Execute with:** `go god mode phase 3`

**Goal:** Every object navigates to its neighbours. This is what makes the Vuln Detail page feel alive.

**Depends on:** Phase 0, Phase 1

| Task | Detail | Status |
|---|---|---|
| 3.1 | Relationship resolver API: `GET /v1/vulnerabilities/:id/related` — same root cause, same author, same rule, regression-of, taint-chained | ✅ |
| 3.2 | Rule accuracy stats endpoint: `GET /v1/rules/:rule_id/stats` — aggregate counts by severity/status | ✅ |
| 3.3 | `<RelatedObjects />` generic panel component — edge type badges (same_rule/same_file/taint_chain), used on Vuln Detail | ✅ |
| 3.4 | Author graph: `GET /v1/authors/:author/vulnerabilities` — open vulns assigned to owner | ✅ |
| 3.5 | Materialised hot-edge tables for Vuln↔Vuln similarity + Vuln↔Author (Postgres materialised views, refresh on scan completion) | ✅ |
| 3.6 | Cmd+K (command palette) upgraded to search across all object types: vulns, rules, repos, authors — live results with `GET /v1/search?q=` | ✅ |

**Shipped files:**
- `alembic/versions/20260522_0020_relationship_views.py` — 4 materialised views
- `DATABASE/database.py` — `refresh_relationship_views`, `get_related_vulnerabilities`, `get_rule_stats`, `get_author_vulnerabilities`, `search_objects`
- `FRONTEND/api/routers/relationships.py` — 4 endpoints + global search
- `FRONTEND/api/main.py` — wired relationships router
- `dashboard/src/lib/api.ts` — `RelatedVuln`, `RelatedResponse`, `RuleStats`, `SearchResult`, `getRelated`, `getRuleStats`, `searchObjects`
- `dashboard/src/lib/queries.ts` — `useRelated`, `useRuleStats`, `useSearch`
- `dashboard/src/components/ui/RelatedObjects.tsx` — `RelatedObjects` + `RelatedObjectsPanel`
- `dashboard/src/components/ui/command-palette.tsx` — live search with section dividers
- `dashboard/src/routes/vuln.$shortId.tsx` — related section replaced with `RelatedObjectsPanel`
- `dashboard/src/styles/acr.css` — `related-edge/sev/rule/file/status--small`, `cmd-section-label`

---

## Phase 4 — Fleet ✅

**Execute with:** `go god mode phase 4`

**Goal:** Absorbs and replaces `/analytics` + `/overview` posture content. Leadership and reporting surface.

**Depends on:** Phase 0, Phase 3

| Task | Detail | Status |
|---|---|---|
| 4.1 | Route `/fleet` — new posture surface, Analytics kept as historical deep-dive | ✅ |
| 4.2 | Posture-over-time chart per repo with overlay repo filter (Trend tab, reuses FindingsTrendChart) | ✅ |
| 4.3 | Coverage: per-repo KPI strip with open/high/med/low/regr/scans counts when repo selected | ✅ |
| 4.4 | Outlier surface: repos with regression spikes, authors above org average (Heatmap tab sidebar) | ✅ |
| 4.5 | Compliance matrix: OWASP Top 10 + CWE Top 25 coverage chips (Compliance tab) | ✅ |
| 4.6 | Repo Risk Heatmap: 2D grid repos × severity columns, opacity-scaled cells | ✅ |
| 4.7 | Auto-STRIDE threat model per repo: 6-threat grid mapped from canonical rule IDs, PDF export | ✅ |
| 4.8 | PDF (window.print) + CSV export for fleet posture + compliance matrix (Export tab) | ✅ |
| 4.9 | Saved views: localStorage-persisted name+repo+tab bookmarks, load via Views menu | ✅ |
| 4.10 | Realtime Fleet: 30s refetchInterval on `useFleet`, manual refresh button | ✅ |

**Shipped files:**
- `FRONTEND/api/routers/fleet.py` — `GET /v1/fleet`, `GET /v1/fleet/compliance`, `GET /v1/fleet/stride/:repo_name`
- `FRONTEND/api/main.py` — wired fleet router
- `dashboard/src/lib/api.ts` — `FleetRepoRow`, `FleetResponse`, `ComplianceRow`, `ComplianceResponse`, `StrideResponse`, `getFleet`, `getFleetCompliance`, `getStride`
- `dashboard/src/lib/queries.ts` — `useFleet`, `useFleetCompliance`, `useStride`
- `dashboard/src/components/charts/RepoHeatmap.tsx` — opacity-scaled 2D heatmap grid
- `dashboard/src/routes/fleet.tsx` — 5-tab fleet page (Heatmap / Compliance / Trend / STRIDE / Export)
- `dashboard/src/routes/_layout.tsx` — Fleet added to Intelligence nav
- `dashboard/src/App.tsx` — `/fleet` route + lazy chunk
- `dashboard/src/components/ui/command-palette.tsx` — Fleet in nav commands
- `dashboard/src/styles/acr.css` — fleet-tabs, heatmap, compliance-grid, stride-grid, print updates

---

## Phase 5 — Workbench ✅

**Execute with:** `go god mode phase 5`

**Goal:** Power-user surface. Learn operation. Rule editor. Ad-hoc analysis. Conversational triage lives here, safely scoped.

**Depends on:** Phase 0, Phase 2, Phase 3

| Task | Detail | Status |
|---|---|---|
| 5.1 | Route `/workbench` — 7-tab power-user surface | ✅ |
| 5.2 | Saved queries: named, localStorage-persisted, parameterized (no raw LLM→SQL) | ✅ |
| 5.3 | NL query interface: regex parser + Groq LLM fallback → structured `WbQueryParams`, runs against DB | ✅ |
| 5.4 | Rule editor: YAML textarea + quick templates (SQL injection / secrets / command inject) + download | ✅ |
| 5.5 | Rule performance: fire_count, TP/FP/rate, noise_ratio, gt_accuracy, avg_confidence table | ✅ |
| 5.6 | Notebook cells: stacked query→table/chart cells, add/remove, table↔bar-chart toggle | ✅ |
| 5.7 | Audit log: org-wide vuln lifecycle event feed (repo/severity/status/triage_verdict) | ✅ |
| 5.8 | API console: endpoint list + path editor + run button + JSON response viewer | ✅ |
| **5.9** | **Ground-truth labelling tool** — TP/FP/TN/FN buttons + reasoning, progress bar, export `.jsonl` | ✅ |
| 5.10 | S5 Predictive Forecasting — **still blocked** (need ≥100 labelled rows from 5.9 first) | 🧊 |
| 5.11 | Triage Chat: NL→params→query→formatted response, Groq LLM toggle | ✅ |
| 5.12 | Attack path composer: BFS taint-chain graph render from `mv_vuln_taint_chain`, depth 1-6 | ✅ |

**Shipped files:**
- `FRONTEND/api/routers/workbench.py` — 7 endpoints: query, nl-query, rule-performance, audit-log, labels (GET/PATCH/export), attack-paths
- `FRONTEND/api/main.py` — wired workbench router
- `dashboard/src/lib/api.ts` — 12 new types + `wbQuery`, `wbNLQuery`, `getRulePerformance`, `getAuditLog`, `getLabels`, `setLabel`, `getAttackPaths`
- `dashboard/src/lib/queries.ts` — `useWbQuery`, `useRulePerformance`, `useAuditLog`, `useLabels`, `useSetLabel`, `useAttackPaths`
- `dashboard/src/routes/workbench.tsx` — 7-tab page: Query/RulePerf/AuditLog/Labelling/RuleEditor/APIConsole/TriageChat
- `dashboard/src/routes/_layout.tsx` — Workbench in Intelligence nav
- `dashboard/src/App.tsx` — `/workbench` route + lazy chunk
- `dashboard/src/components/ui/command-palette.tsx` — Workbench command
- `dashboard/src/styles/acr.css` — wb-cell, wb-table, label-card, gt-btn, rule-editor-textarea, api-console, chat, attack-path

---

## Phase 6 — Trust ✅

**Execute with:** `go god mode phase 6`

**Goal:** Public-facing posture page per repo. The differentiator that makes ACR-QA a platform, not a tool.

**Depends on:** Phase 0, existing attestation infrastructure

| Task | Detail | Status |
|---|---|---|
| 6.1 | Separate URL host / sub-path: public, no auth required | ✅ |
| 6.2 | Posture summary without revealing specific vulns | ✅ |
| 6.3 | Scan freshness + run frequency display | ✅ |
| 6.4 | ECDSA-verifiable attestation chain — in-browser verification without trusting the server | ✅ |
| 6.5 | Compliance status across frameworks | ✅ |
| 6.6 | Embeddable badge `![security](trust.acrqa.com/badge/org/repo)` | ✅ |
| 6.7 | Sign the rendered HTML; link the signature publicly | ✅ |

**Shipped files:**
- `FRONTEND/api/routers/trust.py` — 4 public endpoints (posture, attestation, public-key, badge SVG)
- `dashboard/src/routes/trust.$repoName.tsx` — public trust page with WebCrypto in-browser verification
- `dashboard/src/lib/api.ts` — TrustPosture / TrustAttestation / TrustPublicKey types + getPublic helpers
- `dashboard/src/lib/queries.ts` — useTrustPosture / useTrustAttestation / useTrustPublicKey
- `dashboard/src/App.tsx` — /trust/:repoName route (outside Layout, no auth guard)
- `dashboard/src/styles/acr.css` — .trust-page / .trust-hero / .trust-compliance-row / .trust-verify-badge / etc.

---

## Dependency Map

```
Phase 0 (vuln identity)
   │
   ├── Phase 1 (Vuln Detail) ──────────────────┐
   │                                            │
   ├── Phase 2 (Inbox) ─────────────────────┐  │
   │                                         │  │
   ├── Phase 3 (Relationship layer) ──────┐  │  │
   │                                      │  │  │
   │                                      ▼  ▼  ▼
   │                                    Phase 4 (Fleet)
   │                                    Phase 5 (Workbench)
   │
   └── Phase 6 (Trust) — independent, only needs Phase 0
```

Phase 0 unblocks everything. Phases 1 + 2 make the platform feel coherent first. Phases 4–6 layer on top.

---

## Feature Catalog — Where Old Ideas Live

| Previous item | Now lives in |
|---|---|
| Tier 1.1 PR Risk Predictor | Phase 2.5 — Inbox PR lens |
| Tier 1.2 Time-Travel Analyzer | Phase 1.3 — Vuln Detail timeline + Phase 4.2 — posture-over-time |
| Tier 1.3 Triage Kanban | Phase 2 — Inbox (keyboard queue primary, kanban optional) |
| Tier 1.4 Live SOC View | Phase 4.10 — Realtime Fleet |
| Tier 2.5 Notifications Center | Phase 2.7 — Inbox toasts / desktop notifications |
| Tier 2.6 Webhooks & Integrations | Settings sub-surface (not a phase, added when needed) |
| Tier 2.7 Audit Log | Phase 5.7 — Workbench audit log view |
| Tier 2.8 Command Palette upgrade | Phase 3.6 — Cmd+K searches all object types |
| Tier 3.9 Repo Risk Heatmap | Phase 4.6 |
| Tier 3.10 Attestation Chain Explorer | Phase 1.8 (per-vuln) + Phase 6 (public chain) |
| Tier 3.11 Compliance Matrix | Phase 4.5 |
| Tier 3.12 Custom Rule Editor | Phase 5.4 |
| Tier 3.13 Onboarding Wizard | Independent — build when there's a new-user funnel |
| S1 Attack Path Composer | Phase 5.12 |
| S2 Multi-Model Consensus | Phase 1.5 (Vuln Detail ensemble panel) |
| S3 Conversational Triage | Phase 5.11 |
| S4 Auto-STRIDE Threat Model | Phase 4.7 |
| S5 Predictive Forecasting | Phase 5.10 — **blocked by 5.9 labelling tool** |
| T1 Voice-briefing | Optional layer on Phase 4.10 (realtime Fleet). Tiny feature. |
| T2 Code City (3D) | ❌ Cut. Relationship graph is better. |
| T3 Adversarial Self-Test | Phase 5.5 — rule performance dashboard |

---

## Decision Log

- **2026-05-21** · Plan created with Tier 1–3 feature framing.
- **2026-05-22** · Expanded to include all original Tier 1–3 items + S-Tier.
- **2026-05-22 (rewrite)** · Discarded tier feature-catalog framing. Replaced with architecture-first plan: three shifts + five surfaces. Time estimates removed deliberately.
- **2026-05-22 (phase restructure)** · Reorganised into numbered phases (0–6) each directly invocable with "go god mode phase N". S5 forecasting blocked behind a Phase 5.9 labelling tool pre-req (no ground-truth label data exists anywhere in the codebase).

---

## Open Questions

- [ ] **Fingerprint algorithm** — how aggressive is the AST normalisation? Test on real refactor histories from `TESTS/evaluation/cloned/`.
- [ ] **Backfill strategy** — one-shot re-fingerprint all historical findings, or only new findings forward?
- [ ] **Persistence horizon** — when does a `dismissed` Vulnerability stop appearing? Never / after 1 year / per-user?
- [ ] **Multi-tenancy contract** — same SQL injection pattern in two repos = same Vuln or different? Probably different, but the similarity edge must exist.
- [ ] **URL scheme** — `/vuln/<short-hash>` (opaque, stable) vs `/vuln/<repo>/<rule>/<file>:<line>` (readable, breaks on refactors). Probably first form with redirects.
- [ ] **Existing routes** — keep `/findings`, `/runs/:id` as redirects into new model, or hard-cut on Phase 1 launch?
- [ ] **Persona-aware landing** — self-selected in profile, or inferred from behaviour? Self-select to start.
