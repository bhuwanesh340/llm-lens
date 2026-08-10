# API Contract: Analytics & Health REST API (`/api/v1`)

**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md) | **Data Model**: [data-model.md](../data-model.md)

This is the FastAPI backend's public contract (constitution Principle IV — the
dashboard consumes only this API, never PostgreSQL directly). The LLM gateway
contract itself (OpenAI-compatible `/v1/chat/completions`) is owned by LiteLLM
and is not redefined here — it is consumed as-is per constitution Principle I.

## Conventions

- All endpoints are versioned under `/api/v1`.
- All timestamps are UTC; the frontend converts to local time for display.
- List endpoints accept `page`, `page_size` (`page_size <= 100`), `sort`,
  `order`, and accept the filter parameters below where applicable: `from`,
  `to`, `provider`, `model`, `application_id`, `environment`.
- Errors use a consistent envelope:

  ```json
  {
    "error": {
      "code": "INVALID_DATE_RANGE",
      "message": "The requested date range is invalid.",
      "request_id": "req_123"
    }
  }
  ```

  HTTP status codes: `400, 401, 403, 404, 409, 422, 429, 500, 503` per spec §31.
- Every field documented in [data-model.md](../data-model.md) as
  `NULL`-when-unknown (cost) MUST be serialized as JSON `null` with the
  frontend rendering "Cost unavailable" — never coerced to `0`.
- No endpoint returns prompt/completion text unless content logging has been
  explicitly enabled by the operator (FR-017).

## Health (supports SC-001 setup verification)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Overall liveness+readiness summary |
| GET | `/api/v1/health/live` | Process liveness only |
| GET | `/api/v1/health/ready` | Dependency readiness (DB reachable) |

## Overview (FR-011, FR-012)

`GET /api/v1/overview?from&to&application&environment&provider&model`

Returns: `total_cost` (nullable if any underlying cost unknown — see note),
`total_requests`, `total_tokens`, `avg_latency_ms`, `error_rate`,
`active_models`. `total_cost` MUST distinguish "all costs known" from
"some costs unavailable" in the response so the frontend never sums a `null`
into a false `0`.

## Usage (FR-014)

| Method | Path |
|---|---|
| GET | `/api/v1/usage` |
| GET | `/api/v1/usage/timeseries` |
| GET | `/api/v1/usage/by-model` |
| GET | `/api/v1/usage/by-provider` |

Each returns input/output/total tokens, request counts, and
tokens-per-request, filterable/paginated per Conventions.

## Costs (FR-013)

| Method | Path |
|---|---|
| GET | `/api/v1/costs` |
| GET | `/api/v1/costs/timeseries` |
| GET | `/api/v1/costs/by-model` |
| GET | `/api/v1/costs/by-provider` |
| GET | `/api/v1/costs/by-application` |

Every row carries the known/unavailable cost distinction from data-model.md.

## Requests — Request Explorer (FR-016, FR-017)

| Method | Path |
|---|---|
| GET | `/api/v1/requests` | Paginated list — time, request_id, provider, model, application, tokens, cost, latency, status |
| GET | `/api/v1/requests/{request_id}` | Full detail — includes error info when `status = error`; excludes prompt/response unless content logging enabled |

## Models (FR-015)

| Method | Path |
|---|---|
| GET | `/api/v1/models` |
| GET | `/api/v1/models/{model_id}` | requests, tokens, total cost, avg cost/request, avg latency, P95 latency, error rate |

## Applications (FR-018)

| Method | Path |
|---|---|
| GET | `/api/v1/applications` | |
| POST | `/api/v1/applications` | |
| GET | `/api/v1/applications/{id}` | |
| PATCH | `/api/v1/applications/{id}` | |
| DELETE | `/api/v1/applications/{id}` | |

Requests without an `application_id` MUST appear under a distinct "unassigned"
grouping in list/aggregate responses, never silently omitted (FR-018,
spec.md User Story 4 Acceptance Scenario 3).

## Errors (FR-019)

`GET /api/v1/errors` (+ `by-provider`, `by-model`, `by-code` variants) —
error count, error rate, breakdowns by provider/model/category.

## Authentication (FR-023)

Dashboard/API access requires a session established via operator-configured
admin credentials; session token is a secure HTTP-only cookie (research.md
§4). Unauthenticated requests to any `/api/v1/*` route other than `/health*`
MUST return `401`.
