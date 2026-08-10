<!--
Sync Impact Report
Version change: (template, unratified) → 1.0.0
Modified principles: initial adoption (no prior named principles)
Added sections:
  - Core Principles (I–VI)
  - Technology & Delivery Constraints
  - Development Workflow & Quality Gates
  - Governance
Removed sections: none (first ratified version)
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ reviewed, no changes needed (Constitution Check gate is dynamically filled per feature)
  - .specify/templates/spec-template.md ✅ reviewed, no changes needed (already technology/principle-agnostic)
  - .specify/templates/tasks-template.md ✅ reviewed, no changes needed (already technology/principle-agnostic)
  - .github/prompts/speckit.*.prompt.md ✅ reviewed, no agent-specific (e.g. Claude-only) references found requiring change
Follow-up TODOs: none
-->

# LLM Lens Constitution

## Core Principles

### I. LiteLLM as the Sole Provider Gateway

All LLM provider communication (OpenAI, Anthropic, Gemini, Ollama, or any future
provider) MUST flow through the LiteLLM Proxy's OpenAI-compatible API. Application
code and the FastAPI backend MUST NOT embed provider-specific SDKs or call provider
APIs directly. New provider support is added by extending LiteLLM configuration
(`litellm/config.yaml`), not by writing bespoke provider clients. Rationale: this
keeps retries, model routing, and provider auth in one component and keeps the
platform provider-agnostic, which is the product's core positioning.

### II. Privacy-by-Default Telemetry

The system MUST NOT persist prompt text, completion text, uploaded documents, or
raw provider/API secrets by default. Only normalized request metadata (tokens,
cost, latency, provider, model, status, application, environment) MAY be stored.
Optional content logging (`STORE_PROMPTS`, `STORE_RESPONSES`) MUST default to
`false`, require explicit administrator opt-in, and MUST support redaction and
configurable retention when enabled. API keys MUST be stored only as hashes
(`key_hash`, `key_prefix`), never in plaintext or inside telemetry rows.

### III. Centralized, Auditable Cost Calculation

Cost calculation MUST live in a single pricing/cost service (e.g.
`backend/app/providers/pricing.py` plus one cost service) and MUST NOT be
duplicated in API handlers or the frontend. All persisted financial values
(input/output/total cost) MUST use `Decimal`/PostgreSQL `NUMERIC`, never binary
floating point. When pricing for a provider/model is unknown, cost MUST be
persisted and displayed as unavailable (`NULL` / "Cost unavailable"), never
silently reported as `$0`.

### IV. FastAPI as the Only Control Plane

PostgreSQL is the source of truth for all analytics, and the frontend MUST NOT
query the database directly — every value shown on the dashboard MUST be
obtainable through a documented REST API (`/api/v1/...`). Business logic — cost
calculation, aggregation, database queries — belongs in `app/services/`, not
inside route handlers. The analytics layer MUST consume normalized telemetry
events and MUST NOT branch on provider-specific logic
(`if provider == "openai": ...` is prohibited).

### V. Schema Discipline & Test-First for Financial/Telemetry Code

Every database schema change MUST go through an Alembic migration; manual schema
edits are prohibited. Cost calculations, pricing lookups, token normalization,
event normalization, and redaction logic MUST have unit tests before being
considered done, and integration tests MUST verify the
FastAPI → PostgreSQL → Analytics path. Every public REST endpoint MUST have
API-level tests.

### VI. Incremental Delivery, Simplicity, and Security by Construction

Features MUST be implemented in the phased sequence defined in the project
roadmap (infrastructure → database/telemetry → cost engine → analytics APIs →
dashboard → hardening); each phase MUST leave `docker compose up` and the test
suite in a working state before the next phase begins. The stack MUST NOT
introduce Kafka, Spark, Kubernetes, Celery, Elasticsearch, ClickHouse, or a
microservice split for the MVP — PostgreSQL and the four core services
(postgres, backend, litellm, frontend) are sufficient. All external input MUST
be validated via Pydantic; secrets (API keys, passwords, authorization headers)
MUST never be logged or returned by any API; CORS origins MUST be restricted via
configuration; the application database account MUST NOT be a superuser.

## Technology & Delivery Constraints

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, psycopg 3,
  httpx, structlog, prometheus-client, managed with `uv`.
- Frontend: Next.js 15 + TypeScript (strict mode), Tailwind CSS, shadcn/ui,
  TanStack Query, Recharts, managed with `pnpm`.
- Infrastructure: PostgreSQL 16 is the only mandatory datastore; Redis is
  optional/future and MUST NOT be required for core request processing in v0.1;
  Docker Compose is the primary runtime with required health checks and ordered
  startup (postgres → backend → litellm → frontend).
- All dependency versions, including the LiteLLM proxy image, MUST be pinned or
  bounded (no unbounded ranges such as `litellm>=1`).
- The platform MUST expose `/metrics` (Prometheus) and structured JSON logs in
  production, and MUST expose `/api/v1/health`, `/health/live`, and
  `/health/ready`.
- Non-goals for v0.1 — full prompt management/versioning, fine-tuning, vector
  DB/RAG, agent orchestration, complex RBAC, Kubernetes, distributed
  tracing/OpenTelemetry, automatic ML-based routing, billing integration,
  multi-tenant SaaS billing — MUST NOT be implemented until a later, explicitly
  planned version.

## Development Workflow & Quality Gates

- CI MUST run, in order: lint (ruff / eslint), type-check (mypy / tsc), unit
  tests, integration tests, Docker image build, and a security scan, for both
  backend and frontend.
- Code review MUST verify: no secrets committed, no direct provider-SDK calls
  outside LiteLLM, no cost logic duplicated outside the pricing/cost service,
  migrations included for schema changes, and privacy defaults preserved.
- Every database change ships with an Alembic migration in the same change set
  as the model change.
- API pagination is required for list endpoints (`page_size <= 100`), and
  analytics endpoints MUST support the standard query parameters (`from`, `to`,
  `provider`, `model`, `application_id`, `environment`, `page`, `page_size`,
  `sort`, `order`) using UTC internally.

## Governance

This constitution supersedes ad hoc engineering practices for the LLM Lens
project. Every pull request and every `/speckit.plan` Constitution Check MUST
verify compliance with the principles above; any deviation MUST be recorded and
justified in the plan's Complexity Tracking table.

Amendments are made by editing this file and MUST include: the specific
principle(s) or section(s) changed, a rationale, and a version bump per
semantic versioning:

- **MAJOR**: backward-incompatible governance changes or removal/redefinition
  of a principle.
- **MINOR**: a new principle or materially expanded guidance is added.
- **PATCH**: clarifications or non-semantic wording fixes.

All dependent artifacts (`plan-template.md`, `spec-template.md`,
`tasks-template.md`, and this repository's `speckit.*` command prompts) MUST be
reviewed for consistency whenever a principle is added, removed, or redefined.

**Version**: 1.0.0 | **Ratified**: 2026-08-10 | **Last Amended**: 2026-08-10
