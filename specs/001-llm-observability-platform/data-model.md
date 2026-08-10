# Phase 1 Data Model: LLM Observability Platform (v0.1 Foundation)

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

All monetary fields use `NUMERIC`/`Decimal` (constitution Principle III — never
binary floating point). All tables are managed exclusively through Alembic
migrations (constitution Principle V). This mirrors the source spec's
[Database Design](../../../LLM-Lens-Project-Specification.md#11-database-design)
section, restated with validation rules and relationships.

## Entities

### `LLMRequest` (table: `llm_requests`)

The core observability unit. One row per attempted LLM call (FR-003, FR-004).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID (v7) | Primary key |
| `request_id` | VARCHAR, **unique** | Client/gateway-supplied correlation id; duplicate insert MUST be rejected (Edge Case, research.md §6) |
| `created_at` | TIMESTAMPTZ | Request start |
| `completed_at` | TIMESTAMPTZ, nullable | Null while in-flight |
| `provider` | VARCHAR, FK → `providers.name` | |
| `model` | VARCHAR, FK → `models.model_name` (scoped by provider) | |
| `status` | VARCHAR enum: `success`, `error` | FR-003 requires capture on both paths |
| `input_tokens` | INTEGER, ≥ 0 | |
| `output_tokens` | INTEGER, ≥ 0 | |
| `total_tokens` | INTEGER, ≥ 0 | MUST equal `input_tokens + output_tokens` (validated in normalizer) |
| `input_cost` | NUMERIC(18,8), nullable | `NULL` = pricing unknown (FR-006); `0` = explicit zero-cost model (FR-007) |
| `output_cost` | NUMERIC(18,8), nullable | Same null/zero semantics as `input_cost` |
| `total_cost` | NUMERIC(18,8), nullable | `NULL` iff either component is `NULL` |
| `latency_ms` | INTEGER, ≥ 0 | |
| `ttft_ms` | INTEGER, nullable | Reserved; not required for v0.1 dashboards |
| `application_id` | UUID, nullable, FK → `applications.id` | Null = "unassigned" bucket (FR-018) |
| `environment` | VARCHAR, nullable | Free-form tag (e.g. `production`, `staging`) |
| `api_key_id` | UUID, nullable, FK → `api_keys.id` | |
| `error_type` | VARCHAR, nullable | One of the categories in `ErrorCategory` below |
| `error_code` | VARCHAR, nullable | |
| `error_message` | TEXT, nullable | MUST NOT contain prompt/response content |
| `metadata` | JSONB | Extension point; MUST NOT be used to smuggle prompt/response text unless content logging is explicitly enabled (Principle II) |

**Validation rules**:
- `status = success` ⇒ `error_type`/`error_code`/`error_message` are `NULL`.
- `status = error` ⇒ `error_type` is one of `RATE_LIMIT`, `AUTHENTICATION`,
  `TIMEOUT`, `BAD_REQUEST`, `PROVIDER_ERROR`, `UNKNOWN` (spec §19).
- `total_tokens = input_tokens + output_tokens` (normalizer-enforced, not a DB
  constraint, to tolerate partial provider data gracefully).

**Indexes** (spec §32, needed for FR-011–019 aggregation performance):
`created_at`, `model`, `provider`, `application_id`, `status`, unique on
`request_id`. Composite indexes added later after query profiling.

### `Provider` (table: `providers`)

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `name` | VARCHAR, unique | e.g. `openai`, `anthropic`, `google`, `ollama` |
| `display_name` | VARCHAR | |
| `enabled` | BOOLEAN | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

### `Model` (table: `models`)

Backs the pricing registry (research.md §3) and per-model analytics (FR-015).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `provider_id` | UUID, FK → `providers.id` | |
| `model_name` | VARCHAR | Unique per provider |
| `display_name` | VARCHAR | |
| `input_price_per_1m` | NUMERIC(18,8), nullable | `NULL` = pricing unknown |
| `output_price_per_1m` | NUMERIC(18,8), nullable | `NULL` = pricing unknown |
| `currency` | VARCHAR(3) | Default `USD` |
| `is_active` | BOOLEAN | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

**Validation rule**: a model explicitly configured as zero-cost stores `0`
(not `NULL`) in both price columns, preserving the unknown-vs-zero distinction
required by FR-006/FR-007.

### `Application` (table: `applications`)

Supports FR-018 (application-level attribution).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `name` | VARCHAR | |
| `slug` | VARCHAR, unique | |
| `description` | TEXT, nullable | |
| `environment` | VARCHAR, nullable | Default/primary environment tag |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

### `ApiKey` (table: `api_keys`)

Represents the "API Credential" entity from spec.md. Never stores raw keys
(constitution Principle II).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `key_hash` | VARCHAR | Salted hash only |
| `key_prefix` | VARCHAR | Short, non-secret prefix for display/lookup |
| `name` | VARCHAR | |
| `application_id` | UUID, nullable, FK → `applications.id` | |
| `enabled` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |
| `last_used_at` | TIMESTAMPTZ, nullable | |

## Out of Scope for This Feature

- **`budgets` table**: explicitly deferred per spec.md Assumptions and
  constitution non-goals; not created by this feature's migrations. A future
  feature will introduce it without requiring changes to the entities above.

## Relationships

```text
Provider (1) ───< (many) Model
Application (1) ─< (many) ApiKey
Application (1) ─< (many) LLMRequest   [nullable FK — "unassigned" when absent]
Provider (1) ────< (many) LLMRequest   [by name]
Model (1) ───────< (many) LLMRequest   [by name, scoped to provider]
ApiKey (1) ──────< (many) LLMRequest   [nullable FK]
```

## Aggregation Views (derived, not separate tables)

All dashboard/API aggregates (overview, cost/usage/model/application/error
analytics — FR-011–019) are computed on demand from `llm_requests` joined with
`providers`/`models`/`applications`, per constitution Principle IV
("PostgreSQL is the source of truth… analytics must be reproducible from
stored telemetry"). No pre-aggregated summary tables are introduced in v0.1 to
avoid duplicated-truth risk; this may be revisited if profiling under SC-007's
scale target shows it's needed.
