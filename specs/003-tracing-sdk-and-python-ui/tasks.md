# Tasks: Nested Tracing SDK & Python-Native UI

**Feature Branch**: `003-tracing-sdk-and-python-ui`

**Spec**: [spec.md](./spec.md)

**Depends on**: Feature 002 Phase 1-3 (Project rename + name tagging) — complete. Feature 002 Phase 4 (project API keys) is a hard dependency and is folded into Phase 1 below since nothing here can ship without it.

## Decisions

| Decision | Choice |
| --- | --- |
| Repo layout | Monorepo, two packages: `backend/` (server, existing, grows Jinja+HTMX UI) + new `sdk/` (pip name `llm-lens`, httpx-only) |
| Tracing unit | `Trace` (root) → `Span` (nested, self-referencing parent_span_id) — additive tables, `llm_requests` untouched |
| SDK dependency footprint | `httpx` only. No FastAPI/SQLAlchemy/pydantic-settings in the SDK |
| SDK delivery | Background thread + queue, batched POST, fire-and-forget (never raises into host app) |
| Ingest auth | Project API key (Bearer), reusing feature 002's `api_keys` table/hashing — this is why Phase 4 from 002 moves here |
| UI stack | FastAPI + Jinja2 + HTMX + plain CSS (port the existing teal/lime tokens, no Tailwind build) |
| New tables' JSON/portability | Use SQLAlchemy generic `JSON` (not `JSONB`) so `Trace`/`Span` are SQLite-portable from day one |
| Scope guard | `llm_requests`/React are NOT removed in this feature; React removal is Phase 6, done only after Jinja UI reaches parity |

---

## Phase 1: Foundational — Project API Keys + Trace/Span Model + Ingestion 🎯 BLOCKING

**Goal**: A project-scoped API key can authenticate a batch POST of trace/span data, which is durably and correctly persisted as a nested tree.

**Independent Test**: Issue a project API key, POST a 3-span nested payload to the ingest endpoint, and confirm the trace + all spans are persisted with correct parent linkage and project attribution.

- [X] T201 Implement `ApiKeyService` (generate `llk_` + secret, SHA-256 hash + prefix, verify, revoke, `last_used_at`) in backend/app/services/api_key_service.py (carries forward feature 002 T129)
- [X] T202 [P] Add `ApiKeyCreate`/`ApiKeyResponse`/`ApiKeyCreatedResponse` schemas in backend/app/schemas/api_keys.py (feature 002 T130)
- [X] T203 [P] Implement `POST/GET /api/v1/projects/{id}/keys` + `DELETE /api/v1/keys/{key_id}` in backend/app/api/v1/api_keys.py; register in router (feature 002 T131)
- [X] T204 [P] Create `Trace` model (id: str ULID PK, project_id FK, name, status, started_at, ended_at, duration_ms, metadata JSON) in backend/app/db/models/trace.py (FR-201)
- [X] T205 [P] Create `Span` model (id: str ULID PK, trace_id FK, parent_span_id nullable self-FK, kind, name, status, started_at, ended_at, duration_ms, provider/model/token/cost columns, input/output JSON, error_type/code/message, metadata JSON) in backend/app/db/models/span.py (FR-202, FR-203, FR-204)
- [X] T206 Write Alembic migration creating `traces` and `spans` tables with indexes on `(project_id, started_at)` and `(trace_id, parent_span_id)`
- [X] T207 [P] Add `TraceIngestSpan`/`TraceIngestPayload` (batch of spans + trace metadata) schemas in backend/app/schemas/traces.py
- [X] T208 Implement `verify_project_api_key` FastAPI dependency (Bearer token → project_id, updates `last_used_at`) in backend/app/api/deps.py (FR-216)
- [X] T209 Implement trace/span ingestion service: upsert trace by id, insert-or-ignore spans by id (FR-208 dedup), apply redaction (reuse `apply_redaction` policy) to input/output, resolve project via key precedence (FR-217) in backend/app/services/trace_service.py
- [X] T210 Implement `POST /api/v1/traces/ingest` endpoint wired to `verify_project_api_key` + the ingestion service, returning 401 on bad/revoked key (FR-218) in backend/app/api/v1/traces.py
- [X] T211 [P] Unit tests: span dedup by id, orphan span (parent not yet present) does not error, error status propagation to ancestors in backend/tests/unit/test_trace_service.py (FR-205, FR-207, FR-208)
- [X] T212 [P] API test: ingest with valid/invalid/revoked project key; end-to-end nested payload persists correct tree in backend/tests/api/test_traces_ingest.py

**Checkpoint**: A raw `curl` with a project key and a 3-span JSON body produces a correctly nested trace in the DB.

---

## Phase 2: SDK Package (US1, US2 - P1/P2) 🎯 MVP

**Goal**: `pip install`-able package that decorates functions into a nested trace tree and ships it to the server without ever blocking or breaking host code.

**Independent Test**: In an isolated venv, install only the SDK package, run a decorated 3-level call chain against a running server, and confirm the trace appears correctly nested.

- [X] T213 Create `sdk/pyproject.toml` (package name `llm-lens`, deps: `httpx` only, `requires-python >=3.9`)
- [X] T214 Implement contextvar-based trace/span stack (current trace id, current span id stack) in sdk/llm_lens/context.py (FR-210, FR-211)
- [X] T215 Implement `configure(project=..., api_key=..., base_url=...)` module-level config in sdk/llm_lens/config.py (FR-214, FR-215)
- [X] T216 Implement background batching sender (queue + daemon thread, periodic flush, swallow all network errors) in sdk/llm_lens/sender.py (FR-213, FR-215)
- [X] T217 Implement `@trace(name=...)` decorator (starts/ends a Trace, catches+re-raises exceptions after marking error status) in sdk/llm_lens/tracing.py (FR-210, FR-205)
- [X] T218 Implement `@span(name=..., kind=...)` decorator (nests under current context, same error propagation) in sdk/llm_lens/tracing.py (FR-211, FR-205)
- [X] T219 Implement `set_usage(provider=, model=, input_tokens=, output_tokens=)` to attach LLM fields to the active span in sdk/llm_lens/tracing.py (FR-212)
- [X] T220 Implement no-op fallback path when `configure()` was never called (FR-215) — decorators run the function directly, zero overhead
- [X] T221 [P] Unit tests: nesting order/depth, exception propagation + error marking, no-op-when-unconfigured, sender never raises on connection failure in sdk/tests/test_tracing.py
- [X] T222 [P] Write sdk/README.md with the install + minimal 3-line usage snippet referenced by FR-221's onboarding UI

**Checkpoint**: `pip install ./sdk` in a clean venv + a 10-line script produces a visible trace end-to-end.

---

## Phase 3: Trace Browsing UI (US3 - P1)

**Goal**: Server-rendered pages to list and drill into traces — first slice of the Python-native UI.

**Independent Test**: With recorded traces of mixed depth/status, load the list, filter it, and open one to see an accurate waterfall.

- [X] T223 Add Jinja2 + `python-multipart` to backend deps; wire `Jinja2Templates` + static file mount in backend/app/main.py
- [X] T224 [P] Port the teal/lime dark theme tokens from frontend/src/app/globals.css into backend/app/static/css/theme.css (plain CSS custom properties, no build step) (FR-219)
- [X] T225 [P] Build the base layout template (nav, session-cookie auth check) in backend/app/templates/base.html, reusing `require_admin_session`
- [X] T226 Implement trace list query service (paginated, filter by project/status/time range, includes span_count + total_cost rollup) in backend/app/services/trace_query_service.py
- [X] T227 Implement `GET /traces` server-rendered route + template with HTMX-powered filters (no full page reload) in backend/app/web/traces.py, backend/app/templates/traces/list.html (FR-219)
- [X] T228 Implement trace detail query service (full span tree, ordered for waterfall rendering, orphan spans flagged) in backend/app/services/trace_query_service.py (FR-207)
- [X] T229 Implement `GET /traces/{trace_id}` waterfall view — indent by depth, proportion bars by duration, color by kind/status in backend/app/templates/traces/detail.html (FR-220, FR-222)
- [X] T230 Implement empty-state onboarding (install command + snippet from sdk/README.md) shown when a project has zero traces in backend/app/templates/traces/list.html (FR-221)
- [X] T231 [P] API/route tests for list filtering, pagination, and waterfall nesting/orphan rendering in backend/tests/web/test_traces_ui.py

**Checkpoint**: A real SDK-instrumented script's trace is visible and correctly nested in the browser.

---

## Phase 4: Port Remaining Analytics Views to Jinja (US4 - P3)

**Goal**: Every existing React page has a Python-rendered equivalent, so React can be safely removed.

**Independent Test**: Each of overview/usage/costs/models/requests/projects/errors is reachable and shows equivalent data from the Python UI alone.

- [ ] T232 [P] Port overview page (summary cards + cost timeseries chart) to backend/app/templates/overview.html (server-rendered chart via a lightweight JS chart lib loaded from static assets, no bundler)
- [ ] T233 [P] Port usage page to backend/app/templates/usage.html
- [ ] T234 [P] Port costs page (by-model/by-provider/by-project tabs via HTMX) to backend/app/templates/costs.html
- [ ] T235 [P] Port models list/detail pages to backend/app/templates/models/
- [ ] T236 [P] Port requests list/detail pages to backend/app/templates/requests/
- [ ] T237 [P] Port projects page (create/list/delete + API key management UI) to backend/app/templates/projects.html (feature 002 T133)
- [ ] T238 [P] Port errors page to backend/app/templates/errors.html
- [ ] T239 Port login page to backend/app/templates/login.html, reusing existing session-cookie auth
- [ ] T240 Shared filter-bar partial (date range, project, provider, model, environment) as an HTMX-swappable Jinja include, replacing frontend/src/components/filter-bar.tsx

**Checkpoint**: SC-205 — every current React view has a working Python-rendered equivalent.

---

## Phase 5: Docker/Packaging Cleanup

**Goal**: Remove the Node build/image from the default path; ship the SDK as an installable package.

- [ ] T241 Remove `frontend` service from docker-compose.yml; remove the `Dockerfile`/build context (SC-206)
- [ ] T242 Update root README.md: quickstart now `docker compose up` with just `postgres` + `backend` (+ optional `litellm` profile), plus `pip install ./sdk` usage
- [ ] T243 Delete frontend/ directory once Phase 4 checkpoint is verified against every page
- [ ] T244 Publish sdk/ build metadata (version pin, classifiers) so it is ready for an internal package index or PyPI later

## Phase 6: Validation

- [ ] T245 End-to-end validation: fresh clone → `docker compose up` (no Node) → `pip install ./sdk` → run instrumented script → trace visible in UI (SC-201, SC-206)
- [ ] T246 Validate SC-204 (recomputed trace cost matches displayed total) against a multi-LLM-span trace
- [ ] T247 Validate SC-203 by running instrumented code against a stopped server and confirming zero impact on the host application

---

## Dependencies

```
Phase 1 (API keys + Trace/Span + ingest) ── BLOCKS ──> Phase 2 (SDK)
                                                              │
                                                              v
                                                     Phase 3 (Trace UI)
                                                              │
                                                              v
                                          Phase 4 (port remaining pages)
                                                              │
                                                              v
                                        Phase 5 (drop frontend/, packaging)
                                                              │
                                                              v
                                                  Phase 6 (validation)
```

- **Phase 1 is the hard blocker** — no SDK call succeeds without a working project-keyed ingest endpoint.
- **Phase 2 (SDK) and Phase 3 (UI) are the MVP** — together they deliver the full "install → decorate → see trace" loop (US1/US3, spec priority P1).
- **Phase 4 is required before Phase 5** — React must not be deleted until every page has a proven Python equivalent (SC-205).
- Postgres→SQLite default switch is intentionally **not** in this task list (spec Assumptions) — tracked as a follow-up feature once analytics queries' dialect-specific SQL (`date_trunc`, `percentile_cont`, `JSONB`) is abstracted.
