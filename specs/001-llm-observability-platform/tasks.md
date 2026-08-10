---

description: "Task list for LLM Observability Platform (v0.1 Foundation)"
---

# Tasks: LLM Observability Platform (v0.1 Foundation)

**Input**: Design documents from `/specs/001-llm-observability-platform/`

**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required for user stories), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md), [quickstart.md](./quickstart.md)

**Tests**: The constitution (Principle V) mandates unit tests for cost/pricing/normalization/redaction logic, integration tests for the FastAPI → PostgreSQL → Analytics path, and API tests for every public endpoint. Test tasks below implement that mandate — they are not optional for this feature.

**Organization**: Tasks are grouped by user story (from spec.md, priorities P1–P5) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Paths follow the structure fixed in [plan.md](./plan.md) (`backend/`, `frontend/`, `litellm/`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository, dependency, and container scaffolding

- [X] T001 Create repository structure per plan.md (`backend/`, `frontend/`, `litellm/`, `docs/`, `examples/`, `scripts/`, root `docker-compose.yml`, `.env.example`)
- [X] T002 Initialize backend Python 3.12 project and create a virtual environment where install with `uv` in backend/pyproject.toml (fastapi, sqlalchemy, alembic, pydantic, pydantic-settings, psycopg, httpx, structlog, prometheus-client, pytest, pytest-asyncio, ruff, mypy)
- [ ] T003 [P] Initialize frontend Next.js 15 + TypeScript project with `pnpm` in frontend/package.json (tailwindcss, shadcn/ui, @tanstack/react-query, recharts, react-hook-form, zod, vitest, @testing-library/react, playwright, eslint, prettier)
- [X] T004 [P] Configure backend linting/type-checking (ruff + mypy config) in backend/pyproject.toml
- [ ] T005 [P] Configure frontend linting/formatting/strict TypeScript (eslint, prettier, tsconfig strict mode) in frontend/.eslintrc, frontend/tsconfig.json
- [X] T006 Create docker-compose.yml with postgres, litellm, backend, frontend services, required health checks, and `depends_on` startup ordering (postgres → backend → litellm → frontend)
- [X] T007 [P] Create .env.example with all variables (APP_*, POSTGRES_*, DATABASE_URL, LITELLM_PORT, LITELLM_MASTER_KEY, provider keys, OLLAMA_BASE_URL, NEXT_PUBLIC_API_URL, SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD_HASH, STORE_PROMPTS, STORE_RESPONSES, REQUEST_RETENTION_DAYS)
- [X] T008 [P] Create litellm/config.yaml with example model_list entries for openai/anthropic/gemini/ollama, referencing env vars (no hard-coded keys)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Setup SQLAlchemy base + Alembic migrations framework in backend/app/db/base.py, backend/app/db/session.py, backend/alembic.ini, backend/alembic/env.py
- [X] T010 [P] Create `Provider` model + migration in backend/app/db/models/provider.py
- [X] T011 [P] Create `Model` (pricing) model + migration in backend/app/db/models/model.py
- [X] T012 [P] Create `Application` model + migration in backend/app/db/models/application.py
- [X] T013 [P] Create `ApiKey` model + migration in backend/app/db/models/api_key.py
- [X] T014 Create `LLMRequest` model + migration (FKs to Provider/Model/Application/ApiKey, indexes per data-model.md) in backend/app/db/models/request.py (depends on T010, T011, T012, T013)
- [X] T015 Setup FastAPI app skeleton, pydantic-settings config, structured logging (structlog), and API router mounting in backend/app/main.py, backend/app/core/config.py, backend/app/core/logging.py, backend/app/api/router.py
- [X] T016 [P] Implement admin authentication (bcrypt password check against `ADMIN_PASSWORD_HASH`, secure HTTP-only session cookie) in backend/app/core/security.py
- [X] T017 [P] Implement common Pydantic schemas (pagination envelope, error envelope) in backend/app/schemas/common.py
- [X] T018 Implement health endpoints (`/api/v1/health`, `/health/live`, `/health/ready`) in backend/app/api/v1/health.py
- [X] T019 [P] Setup `/metrics` Prometheus endpoint and base HTTP metrics in backend/app/core/metrics.py
- [X] T020 [P] Setup CORS middleware with configurable origin allowlist in backend/app/main.py
- [ ] T021 [P] Scaffold Next.js app shell (layout, navigation, TanStack Query client, typed API client wrapper) in frontend/app/layout.tsx, frontend/lib/api.ts, frontend/lib/types.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Send a Request and See It Observed (Priority: P1) 🎯 MVP

**Goal**: A developer sends a request through the unified endpoint and sees it appear in the dashboard/API with correct provider, model, tokens, cost, and latency — including correct handling of failures and unknown/zero pricing.

**Independent Test**: Configure one cloud provider and one local (Ollama) provider, send one request through each, and confirm both appear correctly with accurate cost semantics (unavailable vs. zero vs. calculated).

### Tests for User Story 1

- [X] T022 [P] [US1] Unit tests for cost calculation and pricing lookup (known price, unknown price → NULL, zero-cost provider → 0) in backend/tests/unit/test_cost_service.py, backend/tests/unit/test_pricing.py
- [X] T023 [P] [US1] Unit tests for telemetry normalization and redaction (token totals, error categorization, no prompt/response leakage) in backend/tests/unit/test_normalizer.py, backend/tests/unit/test_redaction.py
- [X] T024 [US1] Integration test: request through LiteLLM → telemetry collector → PostgreSQL row, for both success and failure/timeout paths in backend/tests/integration/test_telemetry_pipeline.py

### Implementation for User Story 1

- [X] T025 [P] [US1] Implement pricing registry `get_model_pricing(provider, model)` in backend/app/providers/pricing.py
- [X] T026 [P] [US1] Implement provider registry in backend/app/providers/registry.py
- [X] T027 [US1] Implement normalized telemetry event schema in backend/app/telemetry/events.py
- [X] T028 [US1] Implement telemetry normalizer (token totals, status/error-category normalization) in backend/app/telemetry/normalizer.py (depends on T027)
- [X] T029 [US1] Implement redaction module enforcing default no-prompt/no-response persistence, honoring `STORE_PROMPTS`/`STORE_RESPONSES` in backend/app/telemetry/redaction.py
- [X] T030 [US1] Implement cost service (Decimal-based input/output/total cost, NULL-when-unknown, 0-when-configured-zero-cost) in backend/app/services/cost_service.py (depends on T025)
- [X] T031 [US1] Implement telemetry collector consuming LiteLLM's completion event/callback and persisting normalized `LLMRequest` rows, rejecting duplicate `request_id` in backend/app/telemetry/collector.py (depends on T014, T028, T029, T030)
- [X] T032 [US1] Wire LiteLLM proxy callback/webhook configuration to invoke the telemetry collector in litellm/config.yaml (verify against pinned LiteLLM version's actual callback API per research.md §2)
- [X] T033 [US1] Ensure requests for unconfigured provider/model return a clear, actionable error (FR-025) via LiteLLM config validation and backend error handling
- [X] T034 [US1] Add structured logging for telemetry recording (success/failure), excluding secrets/prompts/responses, in backend/app/telemetry/collector.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — sending a request results in an accurate, privacy-safe, correctly-priced record.

---

## Phase 4: User Story 2 - Analyze Cost and Usage Trends (Priority: P2)

**Goal**: A user filters by time range and sees accurate overview/cost/usage analytics broken down by provider, model, application, environment, and day.

**Independent Test**: With recorded usage spanning multiple days/providers/models, apply each time-range filter and confirm summary metrics, cost breakdowns, and usage breakdowns are internally consistent with the underlying records.

### Tests for User Story 2

- [ ] T035 [P] [US2] API tests for `/api/v1/overview` in backend/tests/api/test_overview.py
- [ ] T036 [P] [US2] API tests for `/api/v1/usage`, `/usage/timeseries`, `/usage/by-model`, `/usage/by-provider` in backend/tests/api/test_usage.py
- [ ] T037 [P] [US2] API tests for `/api/v1/costs`, `/costs/timeseries`, `/costs/by-model`, `/costs/by-provider`, `/costs/by-application` in backend/tests/api/test_costs.py
- [ ] T038 [P] [US2] API tests for `/api/v1/models`, `/models/{model_id}` in backend/tests/api/test_models.py

### Implementation for User Story 2

- [ ] T039 [P] [US2] Implement analytics aggregation service (time-range filtering, group-by provider/model/application/day) in backend/app/services/analytics_service.py
- [ ] T040 [P] [US2] Implement usage aggregation service (tokens by model/provider, tokens-per-request) in backend/app/services/usage_service.py
- [ ] T041 [US2] Implement `GET /api/v1/overview` endpoint in backend/app/api/v1/overview.py (depends on T039)
- [ ] T042 [P] [US2] Implement `/api/v1/usage*` endpoints in backend/app/api/v1/usage.py (depends on T040)
- [ ] T043 [P] [US2] Implement `/api/v1/costs*` endpoints in backend/app/api/v1/costs.py (depends on T039)
- [ ] T044 [US2] Implement `/api/v1/models`, `/models/{model_id}` endpoints (incl. avg latency, P95 latency, error rate per model) in backend/app/api/v1/models.py (depends on T039)
- [ ] T045 [P] [US2] Build frontend overview dashboard page (cards, time-range filter, charts) in frontend/app/dashboard/page.tsx, frontend/components/dashboard/
- [ ] T046 [P] [US2] Build frontend usage analytics page in frontend/app/usage/page.tsx, frontend/components/charts/
- [ ] T047 [P] [US2] Build frontend cost analytics page in frontend/app/costs/page.tsx
- [ ] T048 [P] [US2] Build frontend model analytics page in frontend/app/models/page.tsx
- [ ] T049 [US2] Wire TanStack Query hooks and typed API client calls for overview/usage/costs/models in frontend/lib/api.ts, frontend/hooks/ (depends on T045, T046, T047, T048)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Investigate an Individual Request (Priority: P3)

**Goal**: A user browses, filters, and sorts recorded requests, and opens one to see full detail without exposing prompt/response content by default.

**Independent Test**: With multiple recorded requests (including at least one failure), open the request explorer, filter/sort the list, and open a detail view confirming all fields render correctly and no content is shown unless content logging is enabled.

### Tests for User Story 3

- [ ] T050 [P] [US3] API tests for `/api/v1/requests` list (pagination, filtering, sorting) and `/api/v1/requests/{request_id}` detail (incl. privacy default) in backend/tests/api/test_requests.py

### Implementation for User Story 3

- [ ] T051 [US3] Implement `GET /api/v1/requests` paginated/filterable/sortable list endpoint in backend/app/api/v1/requests.py
- [ ] T052 [US3] Implement `GET /api/v1/requests/{request_id}` detail endpoint, excluding prompt/response unless content logging enabled, including error info when present (depends on T051)
- [ ] T053 [P] [US3] Build frontend request explorer table (pagination, filters, sorting) in frontend/app/requests/page.tsx, frontend/components/tables/
- [ ] T054 [US3] Build frontend request detail view in frontend/app/requests/[request_id]/page.tsx (depends on T053)

**Checkpoint**: All of User Stories 1, 2, AND 3 should now work independently

---

## Phase 6: User Story 4 - Break Down Usage by Application (Priority: P4)

**Goal**: Cost and usage are attributed per application, with requests lacking an application tag grouped as "unassigned."

**Independent Test**: Record usage tagged with at least two application identifiers (plus one untagged request) and confirm application analytics show correct, separately-summed totals including an "unassigned" bucket.

### Tests for User Story 4

- [ ] T055 [P] [US4] API tests for applications CRUD and the "unassigned" grouping behavior in backend/tests/api/test_applications.py

### Implementation for User Story 4

- [ ] T056 [P] [US4] Implement application service (CRUD + attribution aggregation incl. "unassigned" bucket) in backend/app/services/application_service.py
- [ ] T057 [US4] Implement `GET/POST/PATCH/DELETE /api/v1/applications` endpoints in backend/app/api/v1/applications.py (depends on T056)
- [ ] T058 [P] [US4] Build frontend applications analytics page in frontend/app/applications/page.tsx
- [ ] T059 [US4] Add application/environment filter controls to dashboard, usage, costs, and requests views in frontend/components/filters/ (depends on T045-T048, T053)

**Checkpoint**: All of User Stories 1-4 should now work independently

---

## Phase 7: User Story 5 - Understand Errors and Reliability (Priority: P5)

**Goal**: Operators see accurate error counts, rates, and breakdowns by provider, model, and error category.

**Independent Test**: Record a mix of successful and failing requests across at least two error categories, then confirm error analytics reflect correct counts/rates/breakdowns.

### Tests for User Story 5

- [ ] T060 [P] [US5] API tests for `/api/v1/errors` (+ by-provider/by-model/by-code variants) in backend/tests/api/test_errors.py

### Implementation for User Story 5

- [ ] T061 [US5] Extend analytics service with error aggregation (count, rate, by provider/model/category) in backend/app/services/analytics_service.py
- [ ] T062 [US5] Implement `GET /api/v1/errors` (+ variants) endpoints in backend/app/api/v1/errors.py (depends on T061)
- [ ] T063 [P] [US5] Build frontend error analytics page in frontend/app/errors/page.tsx

**Checkpoint**: All 5 user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Retention, observability, documentation, CI, and final validation across all stories

- [ ] T064 [P] Implement `RetentionService` abstraction honoring `REQUEST_RETENTION_DAYS` (no hard-coded retention behavior) in backend/app/services/retention_service.py
- [ ] T065 [P] Add telemetry-specific Prometheus metrics (`llm_lens_telemetry_events_total`, `llm_lens_telemetry_events_failed_total`, `llm_lens_db_query_duration_seconds`) in backend/app/core/metrics.py
- [ ] T066 [P] Write integration examples (Python, JavaScript, cURL, Ollama) in examples/python/, examples/javascript/, examples/curl/, examples/ollama/
- [ ] T067 [P] Write documentation (architecture, development, configuration, providers, telemetry, security, deployment) in docs/architecture.md, docs/development.md, docs/configuration.md, docs/providers.md, docs/telemetry.md, docs/security.md, docs/deployment.md
- [ ] T068 [P] Add GitHub Actions CI workflows (lint, type-check, unit/integration tests, Docker build, security scan) in .github/workflows/backend.yml, .github/workflows/frontend.yml, .github/workflows/docker.yml, .github/workflows/security.yml
- [ ] T069 Add root README.md quick-start, LICENSE (Apache-2.0), CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
- [ ] T070 Execute quickstart.md end-to-end and confirm all measurable outcomes SC-001 through SC-008 in spec.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-7)**: All depend on Foundational phase completion
  - US1 (P1): Can start after Foundational — no dependency on other stories (MVP)
  - US2 (P2): Can start after Foundational — reads `LLMRequest` data produced by US1's pipeline for realistic testing, but its API/UI code has no code dependency on US1's implementation files
  - US3 (P3): Can start after Foundational — same relationship as US2 (data from US1, no code coupling)
  - US4 (P4): Can start after Foundational — its filter-wiring task (T059) touches US2/US3 UI files, so schedule after T045-T048/T053 land
  - US5 (P5): Can start after Foundational — extends the same `analytics_service.py` module as US2 (T039), so sequence after T039 to avoid merge conflicts
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- US1 (P1): Independent (MVP) — no dependency on other stories
- US2 (P2): Independent implementation; benefits from US1 producing real data for validation
- US3 (P3): Independent implementation; benefits from US1 producing real data for validation
- US4 (P4): Independent implementation; its cross-view filter task (T059) touches files created in US2/US3
- US5 (P5): Independent implementation; shares `analytics_service.py` with US2 (sequence, don't parallelize T039/T061)

### Within Each User Story

- Tests (where listed) before implementation
- Models/services before endpoints
- Endpoints before frontend pages that consume them
- Story complete and checkpointed before moving to the next priority

### Parallel Opportunities

- All Setup tasks marked [P] (T003-T008, except T001/T002/T006 which precede them) can run together
- All Foundational model-creation tasks T010-T013 can run in parallel (different files), before T014
- Within US1: T022, T023 (tests) in parallel; T025, T026 in parallel; frontend has no tasks in this story
- Within US2: T035-T038 (tests) in parallel; T039, T040 in parallel; T042, T043 in parallel; T045-T048 (frontend pages) in parallel
- Within US3, US4, US5: marked [P] tasks (tests, independent service/page files) in parallel
- Once Foundational is done, different team members could each take one user story phase (3-7) in parallel, respecting the sequencing notes above for T039/T061 and T045-T048/T053/T059

---

## Parallel Example: User Story 1

```text
# Launch T022, T023 together (different test files):
Task: "Unit tests for cost calculation and pricing lookup in backend/tests/unit/test_cost_service.py, backend/tests/unit/test_pricing.py"
Task: "Unit tests for telemetry normalization and redaction in backend/tests/unit/test_normalizer.py, backend/tests/unit/test_redaction.py"

# Then launch T025, T026 together (different files, no shared dependency):
Task: "Implement pricing registry in backend/app/providers/pricing.py"
Task: "Implement provider registry in backend/app/providers/registry.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run quickstart.md's User Story 1 section independently
5. Deploy/demo if ready — a working unified gateway with accurate, private, cost-aware telemetry is a legitimate MVP

### Incremental Delivery

1. Add User Story 2 → Test independently → Deploy/Demo (cost/usage dashboards)
2. Add User Story 3 → Test independently → Deploy/Demo (request explorer)
3. Add User Story 4 → Test independently → Deploy/Demo (application attribution)
4. Add User Story 5 → Test independently → Deploy/Demo (error analytics)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With Foundational phase complete, up to 5 developers could take one user story phase each; sequence T039-before-T061 (shared `analytics_service.py`) and T059 after the US2/US3 frontend pages it filters.
