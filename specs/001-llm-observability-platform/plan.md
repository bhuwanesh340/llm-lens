# Implementation Plan: LLM Observability Platform (v0.1 Foundation)

**Branch**: `001-llm-observability-platform` | **Date**: 2026-08-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-llm-observability-platform/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Deliver a self-hosted platform that lets a developer send LLM requests through
one OpenAI-compatible endpoint (via LiteLLM) and observe cost, token usage,
latency, and errors for every request in a Next.js dashboard backed by a
FastAPI analytics API and PostgreSQL. Technical approach: LiteLLM proxy owns
provider communication (constitution Principle I); a FastAPI backend
normalizes LiteLLM's request-completion events into a single `llm_requests`
table via a telemetry collector → normalizer → cost service pipeline
(Principle III); all dashboard data is served exclusively through documented
`/api/v1` REST endpoints (Principle IV); the whole stack runs via
`docker compose up --build` with four services (postgres, litellm, backend,
frontend).

## Technical Context

**Language/Version**: Python 3.12.x (backend), TypeScript 5.x on Node.js 22 LTS (frontend)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, pydantic-settings, psycopg 3, httpx, structlog, prometheus-client, LiteLLM (proxy, pinned version) — backend; Next.js 15, Tailwind CSS, shadcn/ui, TanStack Query, Recharts, React Hook Form, Zod — frontend

**Storage**: PostgreSQL 16 (sole mandatory datastore; Redis reserved optional/future, not used in v0.1)

**Testing**: pytest + pytest-asyncio (backend unit/integration/API tests); Vitest + React Testing Library (frontend unit/component tests, research.md §5); Playwright (end-to-end dashboard tests)

**Target Platform**: Linux containers via Docker Compose (self-hosted; single-node deployment)

**Project Type**: Web application (frontend + backend + gateway service)

**Performance Goals**: Dashboard API p95 < 500ms for normal datasets (spec §32); request ingestion must not block the LLM response path

**Constraints**: No prompt/response persistence by default (Principle II); all financial values as `Decimal`/`NUMERIC`, never float (Principle III); list endpoints paginated with `page_size <= 100`; unknown pricing must render as "unavailable," never `$0`

**Scale/Scope**: Single developer/small-team self-hosted deployment; analytics views must remain usable with tens of thousands of historical requests (SC-007); 5 prioritized user stories (P1–P5), 26 functional requirements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate | Status |
|---|---|---|---|
| I | LiteLLM as the Sole Provider Gateway | Backend has no provider SDK code; all provider calls go through LiteLLM proxy; new providers added only via `litellm/config.yaml` | PASS |
| II | Privacy-by-Default Telemetry | `llm_requests` schema (data-model.md) has no prompt/response columns; `STORE_PROMPTS`/`STORE_RESPONSES` default `false`; `api_keys` stores only `key_hash`/`key_prefix` | PASS |
| III | Centralized, Auditable Cost Calculation | Single `pricing.py` + cost service; all cost columns `NUMERIC(18,8)`; unknown pricing → `NULL` (research.md §3, data-model.md) | PASS |
| IV | FastAPI as the Only Control Plane | Frontend consumes only `contracts/api.md` endpoints; no direct DB access from Next.js; business logic lives in `app/services/` | PASS |
| V | Schema Discipline & Test-First | All tables created via Alembic migrations; quickstart.md requires `pytest`/API tests passing before done | PASS |
| VI | Incremental Delivery, Simplicity, Security | 4 services only (no Kafka/K8s/microservices); phased task breakdown expected from `/speckit.tasks`; Pydantic validation, CORS allowlist, non-superuser DB account, secret redaction in logs all required | PASS |

No violations identified. Complexity Tracking table below is empty.

**Post-Phase 1 re-check**: data-model.md, contracts/api.md, and quickstart.md
were reviewed against the same six gates after design — no new violations
introduced (no additional services, no duplicated cost logic, no direct DB
access paths added, all new fields nullable-safe per Principle II/III). Gates
remain PASS.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── alembic.ini
├── app/
│   ├── main.py
│   ├── core/            # config.py, logging.py, security.py, constants.py
│   ├── api/v1/          # health.py, overview.py, usage.py, costs.py, models.py, requests.py, applications.py
│   ├── db/              # base.py, session.py, models/ (request.py, model.py, provider.py, application.py, api_key.py)
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # analytics_service.py, cost_service.py, usage_service.py, model_service.py, application_service.py
│   ├── telemetry/       # events.py, collector.py, normalizer.py, redaction.py
│   └── providers/       # registry.py, pricing.py
├── alembic/versions/
└── tests/
    ├── unit/            # cost calc, pricing lookup, normalization, redaction
    ├── integration/     # FastAPI -> PostgreSQL -> analytics
    └── api/              # every public endpoint

litellm/
├── config.yaml          # model_list, provider routing (constitution Principle I)
└── README.md

frontend/
├── package.json
├── app/                 # dashboard/, usage/, costs/, models/, requests/, applications/, settings/
├── components/          # dashboard/, charts/, tables/, filters/, ui/
├── lib/                 # api.ts, types.ts, utils.ts
├── hooks/
└── tests/               # Vitest unit/component tests; e2e/ for Playwright

docker-compose.yml        # postgres, litellm, backend, frontend (+ redis, optional/disabled)
.env.example
```

**Structure Decision**: Web application layout (Option 2: frontend + backend),
extended with a sibling `litellm/` directory for the gateway's own
configuration (it is a separate Docker Compose service/image, not backend
application code — consistent with constitution Principle I keeping gateway
concerns out of the FastAPI codebase). This matches the repository structure
already fixed in the source specification (`LLM-Lens-Project-Specification.md`
§6) and requires no deviation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — this table is intentionally empty. All six Constitution Check
gates passed without exceptions (see Constitution Check section above).
