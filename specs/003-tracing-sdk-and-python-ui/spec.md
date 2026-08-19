# Feature Specification: Nested Tracing SDK & Python-Native UI

**Feature Branch**: `003-tracing-sdk-and-python-ui`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "pip-installable SDK so anyone can trace LLM calls locally; instead of a separate React UI, build the UI in Python to reduce friction and image weight; tracing model should be nested spans/traces like LangSmith's run tree; when a user installs the SDK and decorates their code, they should see traces, graphs, flows, and tool calls in the LLM Lens UI."

## Context & Relationship to Features 001/002

Feature 001 built gateway-only telemetry: a flat `llm_requests` row per LLM call, captured exclusively via the LiteLLM proxy callback. Feature 002 renamed `Application` → `Project` and added human-readable project tagging with auto-creation.

This feature is a bigger architectural shift, driven by three decisions:

1. **Tracing unit becomes a nested run tree** (`Trace` → `Span` → child `Span`), not a flat request row. A `Span` may represent an LLM call, a tool call, a retrieval step, an embedding call, or a chain/agent step. This is required to show "flows, tool calls, etc." for arbitrary instrumented code, not just gateway-proxied LLM calls.
2. **A pip-installable SDK becomes the primary instrumentation path**, independent of the LiteLLM gateway. Any Python codebase can `pip install llm-lens`, decorate functions, and see traces — the gateway becomes an optional convenience for teams who want a single OpenAI-compatible endpoint, not a requirement.
3. **The dashboard is rebuilt as a server-rendered Python UI** (FastAPI + Jinja2 + HTMX) to eliminate the Node/React build and image, reducing local footprint and setup friction. React/`frontend/` is retired once the new UI reaches parity.

Feature 001's gateway telemetry path (`llm_requests`, `/api/v1/telemetry/events`) and its analytics (cost/usage/error breakdowns) are **not removed** in this feature — they continue to serve gateway-proxied traffic. The new `Trace`/`Span` model is additive. Unifying the two into one analytics surface is called out as an explicit follow-up, not attempted here, to keep this feature shippable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install the SDK and See a Trace (Priority: P1)

A developer with an existing Python codebase installs the tracing SDK, adds a `@trace` decorator to their top-level function and `@span` decorators to the functions it calls (retrieval, an LLM call, a tool call), runs their code once, and immediately sees the full call tree in the LLM Lens UI — including nesting, timing, and which step was the LLM call.

**Why this priority**: This is the entire value proposition of the pivot. Without a working decorator → ingest → UI loop, nothing else matters.

**Independent Test**: In a throwaway script, install the SDK, decorate a 3-level-deep call chain (trace → tool span → LLM span), run it once, and confirm the trace appears in the UI as a waterfall with correct parent/child nesting and durations.

**Acceptance Scenarios**:

1. **Given** the SDK is installed and configured with a project name and server URL, **When** a `@trace`-decorated function runs to completion, **Then** a trace record is created and visible in the UI within a few seconds.
2. **Given** a traced function calls other `@span`-decorated functions, **When** the trace completes, **Then** the UI shows each span nested under its actual caller, in call order, with start time and duration.
3. **Given** a span is marked as an LLM call and reports token usage and model/provider, **When** the trace is viewed, **Then** that span shows token counts and calculated cost using the same pricing rules as gateway-captured requests.
4. **Given** a decorated function raises an exception, **When** the trace is viewed, **Then** the failing span (and its ancestors) are marked as errored, with the error visible, without losing the rest of the trace.
5. **Given** the LLM Lens server is temporarily unreachable, **When** traced code runs, **Then** the traced function's own behavior and return value are completely unaffected — tracing failures are silent to the application.

---

### User Story 2 - Attribute SDK Traces to a Project (Priority: P2)

A developer configures the SDK once with a project name or project API key, and every trace from that process is attributed to that project — consistent with how gateway traces are already tagged (feature 002).

**Why this priority**: Multi-project attribution is the reason projects exist; SDK-based tracing must not be a second, disconnected attribution mechanism.

**Independent Test**: Configure the SDK with a project API key, run traced code, and confirm every resulting trace is attributed to that key's project without any per-call project tag.

**Acceptance Scenarios**:

1. **Given** the SDK is configured with a project API key, **When** traces are sent, **Then** every trace is attributed to that key's project.
2. **Given** the SDK is configured with only a project name (no key), **When** traces are sent, **Then** the project is resolved/auto-created exactly as gateway traces already behave (feature 002 FR-102).
3. **Given** an invalid or revoked project API key is configured, **When** traces are sent, **Then** ingestion is rejected with a clear error surfaced to the SDK's own logging (not raised into the user's application).

---

### User Story 3 - Browse and Drill Into Traces in the UI (Priority: P1)

A developer opens the LLM Lens UI, sees a list of recent traces across projects, filters by project/status/time range, and opens one trace to see a visual waterfall of every span, its timing, inputs/outputs (when content logging is enabled), and any errors.

**Why this priority**: Equal priority to US1 — an SDK that reports traces nobody can view delivers no value.

**Independent Test**: With several recorded traces of varying depth and status, open the trace list, filter it, and open one trace to confirm the waterfall accurately reflects the recorded span tree.

**Acceptance Scenarios**:

1. **Given** traces exist, **When** the user opens the traces list, **Then** it shows time, project, name, duration, span count, status, and total cost per trace, paginated.
2. **Given** a trace is selected, **When** its detail view opens, **Then** a waterfall shows every span indented by nesting depth, proportioned by duration, colored by span kind and status.
3. **Given** content logging is disabled (the default), **When** a span is expanded, **Then** no input/output content is shown, consistent with feature 001's privacy default.
4. **Given** a trace contains an errored span, **When** viewed, **Then** the error is visually distinguishable in the waterfall and its detail is shown on expansion.
5. **Given** no traces exist yet, **When** the page loads, **Then** it shows onboarding guidance (install command + minimal code snippet) rather than an empty table.

---

### User Story 4 - Run the Whole Platform Without Node or a Heavy Frontend Image (Priority: P3)

An operator starts LLM Lens locally and gets the full UI experience from a single Python process, without a Node build step, a separate frontend container, or a multi-minute Docker image build.

**Why this priority**: This is the packaging/friction goal driving the pivot, but it is validated by removing the React app only after the Python UI reaches parity — it is sequenced after US1/US3 are solid.

**Independent Test**: Start the server with a single command against a fresh environment and confirm every user-facing view (traces, and the existing analytics pages once ported) is served from the one process with no Node tooling involved.

**Acceptance Scenarios**:

1. **Given** a fresh checkout, **When** the server is started, **Then** no Node/pnpm install or build step is required to see the full UI.
2. **Given** the Python UI has reached parity with the existing React pages, **When** the React app is removed, **Then** every previously available view remains reachable with equivalent information.
3. **Given** the operator wants the OpenAI-compatible gateway, **When** they opt in, **Then** it runs as an additional, clearly optional component — not a requirement to see traces.

---

### Edge Cases

- What happens when a span's parent trace never completes (process crash mid-trace)? The trace must still show whatever spans were successfully sent, marked incomplete, rather than vanishing entirely.
- What happens when spans arrive out of order (child ingested before parent, or parent never arrives)? The UI must degrade gracefully — showing an orphaned span rather than failing to render the trace.
- What happens when a deeply nested or very wide trace (many spans) is viewed? The waterfall must remain usable (scrollable/collapsible) rather than becoming unreadable or freezing the page.
- What happens when the SDK is used without any configuration (no project, no server URL)? Tracing must no-op safely rather than raising into the host application.
- What happens when the same span ID is reported twice (retry from the SDK's batching sender)? The server must not create duplicate spans.
- How does the system behave when a trace mixes gateway-sourced requests and SDK-sourced spans for the same logical project? Both must be attributable to the same project even though they are recorded through different paths.

## Requirements *(mandatory)*

### Functional Requirements

#### Nested tracing model

- **FR-201**: System MUST represent one top-level unit of instrumented work as a `Trace`, containing an ordered tree of `Span`s.
- **FR-202**: System MUST allow a `Span` to have a parent `Span`, forming an arbitrarily nested call tree within a `Trace`.
- **FR-203**: Each `Span` MUST record a kind (at minimum: LLM call, tool call, retrieval, embedding, chain/agent step, or generic/custom), a name, status, start time, and duration.
- **FR-204**: A `Span` of kind "LLM call" MUST support the same token/cost fields as feature 001's request records (provider, model, input/output/total tokens, input/output/total cost), using the same centralized pricing and unknown/zero-cost rules.
- **FR-205**: System MUST mark a `Span` (and propagate to ancestor spans/trace) as errored when the instrumented code raises, without discarding sibling spans already recorded.
- **FR-206**: System MUST NOT persist span input/output content by default, consistent with feature 001's privacy-by-default principle, and MUST support the same explicit opt-in for content logging.
- **FR-207**: System MUST tolerate spans arriving without their parent yet present (or never arriving) by rendering them as identifiable orphans rather than failing.
- **FR-208**: System MUST de-duplicate a span submitted more than once under the same identifier.

#### SDK

- **FR-209**: System MUST provide a pip-installable client package, independent of the server package, with no server-side dependencies (no web framework, no ORM, no database driver).
- **FR-210**: The SDK MUST provide a decorator or equivalent construct that starts a `Trace` for a top-level function and ends it when the function returns or raises.
- **FR-211**: The SDK MUST provide a decorator or equivalent construct that starts a nested `Span` under the current trace/span context for any function, without the caller manually passing trace/span identifiers.
- **FR-212**: The SDK MUST provide a way to attach LLM-specific fields (provider, model, token usage) to the current span.
- **FR-213**: The SDK MUST send trace/span data to the server asynchronously/in the background, such that a slow or unreachable server never delays or breaks the host application's own execution.
- **FR-214**: The SDK MUST support configuring a project by name or by project API key, consistent with feature 002's attribution model.
- **FR-215**: The SDK MUST no-op safely (instrumented functions still run and return normally) when unconfigured or when the server is unreachable.

#### Ingestion & attribution

- **FR-216**: System MUST provide an ingestion endpoint for trace/span batches, authenticated via a project API key.
- **FR-217**: System MUST attribute every ingested trace to a project using the same name-resolution/auto-creation and key-precedence rules established in feature 002.
- **FR-218**: System MUST reject ingestion with a clear, actionable error when authentication is invalid, without ever partially attributing traces to the wrong project.

#### UI

- **FR-219**: System MUST provide a server-rendered UI (no separate frontend build/runtime) for browsing traces, filtering by project/status/time range, and viewing a single trace's span waterfall.
- **FR-220**: System MUST visually distinguish span kind and status in the waterfall view.
- **FR-221**: System MUST show onboarding guidance (install + minimal usage snippet) when no traces exist yet.
- **FR-222**: System MUST NOT display span input/output content in the UI unless content logging has been explicitly enabled, consistent with FR-206.
- **FR-223**: System MUST continue to serve every analytics view already delivered by features 001/002 (overview, usage, costs, models, requests, projects, errors) from the same Python-rendered UI before the React app is removed.

### Key Entities

- **Trace**: One top-level instrumented unit of work — a name, project attribution, overall status, start/end time, and the root of a span tree.
- **Span**: One step within a trace — kind, name, parent span (optional), status, timing, and (for LLM-kind spans) token/cost fields. Spans nest to form the call tree.
- **SDK Client Configuration**: Project attribution (name or API key), server URL, and background delivery settings held in the instrumented process; never persisted server-side beyond the resulting traces/spans.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-201**: A developer can go from `pip install` to seeing a correctly nested trace in the UI using only decorators, with no server-side code changes.
- **SC-202**: 100% of spans within a successfully delivered trace render at their correct nesting depth and in call order.
- **SC-203**: Tracing overhead never blocks or breaks the host application, including when the server is completely unreachable for the entire run.
- **SC-204**: A trace's total cost, recomputed from its LLM-kind spans, matches the displayed total with zero discrepancy.
- **SC-205**: Every view available in the current React dashboard remains available in the Python UI before `frontend/` is removed.
- **SC-206**: Starting the platform locally requires no Node/pnpm installation or build step.

## Assumptions

- The SDK's decorator-based API is the primary interface; automatic instrumentation of specific third-party LLM client libraries (e.g. wrapping an OpenAI client automatically) is a valuable follow-up but not required for this feature's initial release.
- Unifying gateway-sourced `llm_requests` analytics with the new `Trace`/`Span` model into one combined analytics surface is out of scope for this feature; both coexist, and gateway traffic continues to be visible in the existing analytics views.
- SQLite-as-default and removal of the Postgres-only assumptions in existing analytics queries is a valuable follow-up (tracked separately) but not a hard requirement of this feature; the new `Trace`/`Span` model is written to be dialect-agnostic from the start so that follow-up is additive, not a rewrite.
- The LiteLLM gateway remains a supported, opt-in component; it is not required to use the SDK or view traces.
- Distributed tracing across process/service boundaries (propagating a trace context over the network) is out of scope; a trace is scoped to a single process invocation for this feature.
