# Phase 0 Research: LLM Observability Platform (v0.1 Foundation)

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Most technical decisions for this feature are already pinned by the ratified
[constitution](../../.specify/memory/constitution.md) and the source
[LLM Lens Project Specification](../../../LLM-Lens-Project-Specification.md), so
this research phase focuses on the small number of decisions those documents
leave open, plus a rationale/alternatives record for the load-bearing choices.

## Decisions

### 1. Overall architecture shape

- **Decision**: Four Docker Compose services — `postgres`, `litellm`, `backend`
  (FastAPI), `frontend` (Next.js) — with `redis` reserved as an optional/future
  service, not started in v0.1.
- **Rationale**: Constitution Principle VI and the source spec's non-goals
  explicitly prohibit a microservice split, queues, or Kubernetes for the MVP;
  four services is the minimum needed to satisfy FR-001/002 (gateway),
  FR-003–010 (telemetry/cost, backend+db), and FR-011–019 (dashboard).
- **Alternatives considered**: Single combined backend+gateway process
  (rejected — LiteLLM ships as its own proxy image and reimplementing it would
  violate Principle I); adding Redis/Celery now for async telemetry writes
  (rejected — unnecessary at MVP scale per Principle VI and SC-007's
  "tens of thousands of requests" scale target).

### 2. Telemetry capture mechanism

- **Decision**: Use LiteLLM's proxy callback/hook mechanism to emit a raw event
  after each request completes (success or failure), which the backend's
  telemetry collector (`app/telemetry/collector.py`) receives, normalizes
  (`normalizer.py`), prices (`cost_service.py`), and persists.
- **Rationale**: Constitution Principle I forbids reimplementing provider APIs;
  LiteLLM already emits token usage and provider/model metadata per request.
  The exact callback API name/shape MUST be verified against the pinned
  LiteLLM version at implementation time (constitution Rule: "do not invent
  LiteLLM APIs") rather than assumed here.
- **Alternatives considered**: Polling provider APIs for usage after the fact
  (rejected — not all providers expose this, and it breaks the "telemetry for
  every request including local Ollama" requirement, FR-002); having the
  frontend or client report usage (rejected — untrusted, violates FR-003's
  "every request attempted" guarantee for failures/timeouts).

### 3. Pricing/unknown-cost handling

- **Decision**: A single pricing registry (`app/providers/pricing.py`) exposes
  `get_model_pricing(provider, model) -> ModelPricing | None`. When `None`,
  the cost service persists `NULL` for cost fields; the API/dashboard render
  "Cost unavailable" instead of `$0`. Zero-cost providers (e.g. Ollama) are
  modeled as an explicit `ModelPricing(input=0, output=0)` entry, not as
  "unknown."
- **Rationale**: Directly satisfies FR-006/FR-007 and constitution Principle
  III; keeps the "unknown vs. zero" distinction unambiguous at the data layer
  instead of being inferred in the UI.
- **Alternatives considered**: Defaulting unknown pricing to `$0` (rejected —
  explicitly prohibited by spec section 12.2 and FR-006).

### 4. Authentication approach for v0.1

- **Decision**: Single operator-configured admin credential
  (`ADMIN_EMAIL` / bcrypt `ADMIN_PASSWORD_HASH`), session via secure
  HTTP-only cookie issued by the FastAPI backend. No multi-user/RBAC.
- **Rationale**: FR-023 requires operator-configured credentials (no hard-coded
  defaults); constitution non-goals defer RBAC/SSO/OAuth to a later version.
- **Alternatives considered**: JWT bearer tokens in local storage (rejected —
  more XSS-exposed than HTTP-only cookies for a browser dashboard); no auth at
  all (rejected — violates FR-023 and OWASP baseline expectations for an
  exposed dashboard).

### 5. Frontend testing framework

- **Decision**: Vitest + React Testing Library for frontend unit/component
  tests; Playwright for end-to-end tests (already specified in source spec
  section 35).
- **Rationale**: Source spec pins `pnpm test`/`pnpm lint`/`pnpm typecheck` but
  does not name a unit test runner; Vitest is the current standard pairing
  with Next.js 15 + TypeScript strict mode and integrates with the existing
  `pnpm` toolchain without extra config overhead.
- **Alternatives considered**: Jest (rejected — slower with the Next.js/ESM
  toolchain already implied by Next 15/TS 5, no functional advantage here).

### 6. Request identifier uniqueness (Edge Case)

- **Decision**: `request_id` is a database-unique column; a duplicate
  client-supplied `request_id` is rejected by the telemetry collector with a
  logged conflict (HTTP 409-style internal handling), not silently overwritten.
- **Rationale**: Matches the `llm_requests.request_id VARCHAR UNIQUE`
  constraint already specified in source spec section 11.1 and the Edge Case
  in spec.md.

## Open Items Deferred to Implementation (not blocking this plan)

- Exact pinned LiteLLM proxy image tag/version (constitution requires pinning
  after validating the current stable release at implementation time — not a
  planning-time decision).
- Exact Prometheus histogram buckets for latency metrics — implementation
  detail, not required to satisfy any FR/SC.

No `NEEDS CLARIFICATION` markers remain — all Technical Context fields in
[plan.md](./plan.md) are resolved above or directly sourced from the
constitution.
