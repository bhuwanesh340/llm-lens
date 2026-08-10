# Quickstart: Validate the LLM Observability Platform (v0.1)

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This validates the feature end-to-end against the acceptance scenarios in
[spec.md](./spec.md). It assumes the implementation phases in
[plan.md](./plan.md) are complete through at least Phase 3 (Cost Engine).

## Prerequisites

- Docker + Docker Compose installed.
- (Optional, for zero-cost local testing) [Ollama](https://ollama.com)
  installed with a model pulled, e.g. `ollama pull llama3.2`.
- (Optional) An API key for at least one cloud provider (OpenAI/Anthropic/
  Gemini) if validating paid-provider cost calculation.

## Setup

```powershell
git clone <repo-url> llm-lens
cd llm-lens
Copy-Item .env.example .env
# Edit .env: set ADMIN_EMAIL / ADMIN_PASSWORD_HASH, provider keys as desired
docker compose up --build
```

Verify health (SC-001 — first-request-in-under-10-minutes target):

```powershell
curl http://localhost:8000/api/v1/health
```

## Validate User Story 1 — Send a request, see it observed

```powershell
curl http://localhost:4000/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer anything" `
  -d '{"model":"gpt-4.1","messages":[{"role":"user","content":"Explain vector databases."}]}'
```

- Open `http://localhost:3000` → the request MUST appear within 5 seconds
  (SC-002) with provider, model, tokens, cost, latency populated.
- Repeat against a model with no pricing configured → cost MUST render as
  "Cost unavailable", not `$0` (SC-008).
- Repeat against the local Ollama model (if configured) → cost MUST render as
  exactly `$0.00` (Edge Case: zero-cost provider).
- Send a request to an unconfigured model name → MUST receive a clear error,
  not a hang or silent failure (Edge Case).

## Validate User Story 2 — Cost/usage analytics

- In the dashboard, switch the time-range filter across 24h/7d/30d/custom and
  confirm totals change consistently with the requests sent.
- Open `/costs` and `/usage`; confirm per-provider/per-model breakdowns sum to
  the displayed total (SC-003 — reproducibility).

## Validate User Story 3 — Request explorer

- Open `/requests`, locate the request(s) sent above, open detail view.
- Confirm no prompt/response text is shown (default privacy — FR-008, SC-005).
- If `STORE_PROMPTS`/`STORE_RESPONSES` are enabled in `.env` and the stack is
  restarted, confirm content appears only then.

## Validate User Story 4 — Application breakdown

- Send requests tagged with two different `application` values (via the
  gateway's metadata/header mechanism configured for the deployment).
- Confirm `/applications` shows separate totals per application, and a
  request sent without an application tag appears under "unassigned".

## Validate User Story 5 — Error analytics

- Trigger at least two distinct failure types (e.g., an invalid model name for
  `BAD_REQUEST`, and an invalid API key for `AUTHENTICATION`).
- Confirm `/errors` shows correct counts, rates, and category breakdown.

## Automated Checks

```powershell
# Backend
cd backend
uv run ruff check .
uv run mypy .
uv run pytest

# Frontend
cd ../frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

All of the above MUST pass before the feature is considered done, per
constitution Principle V and the Development Workflow & Quality Gates section.
