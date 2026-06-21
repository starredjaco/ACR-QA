# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands assume you are in the repo root with `.venv` active.

### Backend

```bash
# Run the full pytest suite (fast tests only — skips @slow by default)
.venv/bin/pytest TESTS/ -v --tb=short

# Run a single test file
.venv/bin/pytest TESTS/test_normalizer.py -v

# Run a single test by name
.venv/bin/pytest TESTS/test_normalizer.py -k "test_canonical_finding" -v

# Run slow evaluation tests explicitly
.venv/bin/pytest TESTS/ -m slow -v

# Run ALL tests including slow (mirrors nightly CI)
.venv/bin/pytest TESTS/ --override-ini="addopts=" -v

# Lint + auto-fix
.venv/bin/ruff check CORE/ DATABASE/ FRONTEND/ TESTS/ --fix
.venv/bin/ruff format CORE/ DATABASE/ FRONTEND/ TESTS/

# Type check (CORE/ only — annotations are enforced here)
.venv/bin/mypy CORE/ --ignore-missing-imports

# Start the FastAPI server (port 8000, hot-reload)
.venv/bin/uvicorn FRONTEND.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run a one-off analysis via CLI
python CORE/main.py --target-dir TESTS/samples/comprehensive-issues --repo-name my-repo

# Database migrations
alembic upgrade head
alembic downgrade -1

# Eval integrity check
make eval-audit
```

### Frontend (dashboard/)

```bash
cd dashboard

npm run dev           # Vite dev server on :5173
npm run build         # TypeScript compile + Vite bundle
npm run test          # Vitest unit tests (one-shot)
npm run test:watch    # Vitest in watch mode
npm run test:e2e      # Playwright E2E tests
npm run lint          # ESLint

# Regenerate typed API client from live FastAPI spec
npm run generate-api  # requires FastAPI running on :8000
```

### Pre-commit

```bash
# Install hooks (one-time)
.venv/bin/pre-commit install

# Run all hooks against all files manually
.venv/bin/pre-commit run --all-files
```

Hook chain on every commit: `trailing-whitespace → end-of-file-fixer → check-yaml (excludes deploy/helm/) → check-json → check-merge-conflicts → debug-statements → ruff format --check → ruff lint → mypy CORE/ → pytest (fast, excludes slow/exploit/e2e)`.

### Change Protocol (mandatory before every commit)

After ANY change — bug fix, new feature, adapter tweak, evaluation update:

1. **Test new + old:** run the fast suite (`pytest TESTS/ -q --tb=short`). If the change touches an engine, also run the specific test file for that engine. If it adds a new code path, write or confirm a test covers it.
2. **Document:** update every relevant MD — `docs/CHANGELOG.md` (version entry), `docs/ACTIVE_ROADMAP.md` (mark task done if applicable), `docs/GOD_MODE_V11_PERFECT_TEN_ALL_PERSPECTIVES.md` (update phase status if applicable), and `CLAUDE.md` if the change affects dev workflow.
3. **Then commit:** only after steps 1 and 2 are done. One logical change per commit. Never batch unrelated changes into one commit.

```bash
# Minimum checklist before every commit:
.venv/bin/ruff format CORE/ DATABASE/ FRONTEND/ TESTS/
.venv/bin/ruff check CORE/ DATABASE/ FRONTEND/ TESTS/ --fix
.venv/bin/mypy CORE/ --ignore-missing-imports
.venv/bin/pytest TESTS/ -q --tb=short
# → update CHANGELOG.md → commit
```

---

## Architecture

### Pipeline flow

```
CLI / GitHub Action
       │
       ▼
CORE/main.py          ← orchestrator; reads .acrqa.yml config
       │
       ├─ LanguageAdapter (CORE/adapters/)
       │     python_adapter.py  → ruff, semgrep, vulture, radon, bandit, jscpd
       │     js_adapter.py      → ESLint/semgrep (JS/TS)
       │     go_adapter.py      → staticcheck
       │
       ├─ CORE/detection/tool_runner.py    ← subprocess orchestration
       │
       ├─ CORE/engines/normalizer.py       ← raw tool JSON → CanonicalFinding (Pydantic)
       │     RULE_MAPPING dict maps tool-specific rule IDs to canonical IDs (e.g. B101 → SECURITY-002)
       │
       ├─ CORE/engines/taint_analyzer.py   ← inter-procedural taint (sources/sinks/sanitizers from config/)
       │
       ├─ CORE/engines/quality_gate.py     ← evaluates findings against .acrqa.yml thresholds
       │
       ├─ CORE/engines/explainer.py        ← RAG-grounded AI explanation via Groq (llama3-8b-8192)
       │
       ├─ CORE/engines/attestation.py      ← ECDSA-signed provenance for each scan
       │
       └─ DATABASE/database.py             ← PostgreSQL storage via psycopg2 connection pool
```

### CanonicalFinding — the central data contract

Defined in `CORE/engines/normalizer.py`. Every tool output is converted to this Pydantic model before any downstream engine sees it. Key fields:

```python
finding_id: str          # UUID
fingerprint: str         # dedup hash
canonical_rule_id: str   # e.g. "SECURITY-001" — from RULE_MAPPING
original_rule_id: str    # tool-native rule ID
severity: str            # "high" | "medium" | "low"
category: str
file: str
line: int
language: str
message: str
evidence: dict           # snippet + context_before + context_after
tool_raw: dict           # unmodified tool output
```

Never add fields to `CanonicalFinding` without updating RULE_MAPPING and the corresponding Pydantic validators. Inter-engine communication must go through this type.

### FastAPI layer (FRONTEND/api/)

```
FRONTEND/api/main.py       ← FastAPI app; mounts routers; OTel + Sentry init (degrades silently when env vars absent)
FRONTEND/api/routers/
    auth.py                ← /v1/auth/* (JWT-based, passlib bcrypt)
    runs.py                ← /v1/runs/* (past scan results)
    scans.py               ← /v1/scans/* (trigger + stream progress via SSE)
FRONTEND/api/deps.py       ← get_current_user(), get_db() FastAPI dependencies
FRONTEND/api/models.py     ← Pydantic request/response models (separate from CanonicalFinding)
DATABASE/database.py       ← ThreadedConnectionPool(1,10); env: DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD
```

All data endpoints require a JWT (`Authorization: Bearer <token>`). Public: `GET /health`, `GET /docs`, `GET /openapi.json`.

### React dashboard (dashboard/src/)

- **Routing:** react-router-dom v7; routes in `src/routes/`; `_layout.tsx` is the shell with sticky header + nav
- **State:** TanStack Query v5 for server state; zustand for auth store (`src/lib/auth.ts`)
- **Styling:** Tailwind CSS v3 only; tokens via CSS custom properties in `src/styles/globals.css`; `cn()` helper = `twMerge(clsx(...))` in `src/lib/utils.ts`
- **Components:** shadcn-style primitives in `src/components/ui/` using `cva`; feature components in `findings/`, `scans/`, `supply/`, `compliance/`
- **Icons:** lucide-react only — always `aria-hidden` on decorative use
- **i18n:** react-i18next; English + Arabic (RTL via `[dir="rtl"]` CSS overrides); `setLanguage()` in `src/lib/i18n.ts`
- **Live progress:** SSE via `src/lib/sse.ts` → `EventSource` connected to `/v1/scans/{id}/stream`
- **API types:** generated from FastAPI OpenAPI spec via `npm run generate-api` → `src/lib/api-schema.d.ts`

### Taint analysis config

Taint sources, sinks, and sanitizers are YAML files in `config/`:

- `config/taint_sources.yml` — HTTP inputs, env vars, file reads treated as tainted
- `config/taint_sinks.yml` — dangerous calls (SQL execute, subprocess, eval, etc.)
- `config/taint_sanitizers.yml` — functions that sanitize taint (html.escape, parameterize, etc.)

Edit these instead of hardcoding patterns in `taint_analyzer.py`.

### Services (docker-compose.yml)

| Service | Port (host) | Purpose |
|---------|------------|---------|
| postgres | 5434 | Primary DB (`acrqa` database) |
| redis | 6380 | Rate limiting + Celery broker |
| app (Flask legacy) | 5000 | Legacy dashboard |
| FastAPI | 8000 | Primary API |
| Prometheus | 9090 | Metrics scrape |
| Grafana | 3001 | Dashboards |

### Environment variables

Key vars (copy `.env.example` → `.env`):

```
GROQ_API_KEY_1          # required for AI explanations
DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD
REDIS_HOST / REDIS_PORT
SECRET_KEY              # JWT signing
ACRQA_JSON_LOGS=1       # switch to structured JSON logging
OTEL_EXPORTER_OTLP_ENDPOINT   # optional; enables OpenTelemetry tracing
SENTRY_DSN              # optional; enables Sentry error reporting
```

### Test markers

```
(default)    fast unit/integration tests
slow         full pipeline against real repos (minutes) — run with -m slow
integration  requires live Postgres + Redis
exploit      requires Docker daemon
smoke        requires ACRQA_TEST_URL env var pointing to a live deployment
e2e          requires FastAPI running on :8000
offline      requires Ollama running locally
```

### Directory conventions

- `CORE/` — all Python analysis logic; mypy is enforced here
- `CORE/engines/` — detection + scoring + AI engines
- `CORE/adapters/` — language-specific tool wrappers (extend `LanguageAdapter` ABC)
- `CORE/detection/` — subprocess tool runner + code extractor + egress guard
- `CORE/utils/` — metrics, rate limiter
- `DATABASE/` — psycopg2 interface + Alembic migrations
- `FRONTEND/` — FastAPI app + legacy Flask; mypy is **not** enforced here
- `TESTS/` — all pytest tests; mirrors CORE/ structure loosely
- `TESTS/samples/` — intentionally vulnerable Python files used by unit tests
- `TESTS/evaluation/` — hold-out eval harness (`test_recall.py`); cloned repos land in `TESTS/evaluation/cloned/` (gitignored)
- `dashboard/` — React/Vite SPA
- `config/` — YAML taint rules + Prometheus/Grafana configs
- `deploy/` — Helm chart + Terraform AWS stack
- `DATA/outputs/` — tool output JSON files (gitignored)
