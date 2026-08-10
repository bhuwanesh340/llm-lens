# LiteLLM Gateway

This directory contains the LiteLLM Proxy configuration for LLM Lens
(constitution Principle I — LiteLLM is the sole provider gateway).

- `config.yaml` — `model_list` (provider/model routing) and
  `litellm_settings.callbacks`, which wires request telemetry to the
  backend.
- `custom_callbacks.py` — a `CustomLogger` implementation that POSTs a
  normalized event to the backend's `POST /api/v1/telemetry/events` webhook
  after every completed request (success or failure). It does not persist
  or transform data itself; all normalization, redaction, and cost
  calculation happen in the backend (`app/telemetry/`, `app/services/`).

## Adding a new provider/model

1. Add an entry to `model_list` in `config.yaml`, referencing credentials
   via `os.environ/VAR_NAME` (never hard-code secrets).
2. Add the corresponding row to the backend `models`/`providers` tables
   (via an Alembic migration or the `/api/v1/applications`-style admin
   tooling) so the pricing registry and telemetry collector recognize it —
   otherwise requests for that model are rejected with a clear
   "unconfigured model" error (FR-025).

## Required environment variables

See the root `.env.example` for the full list (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`,
`LITELLM_MASTER_KEY`, `LITELLM_CALLBACK_TOKEN`, `BACKEND_TELEMETRY_URL`).
