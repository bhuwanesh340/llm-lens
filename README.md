# LLM Lens

Self-hosted LLM observability platform. Route every LLM call through a single gateway and get accurate cost, token, latency, and error analytics — without ever persisting prompt/response content by default.

**Stack:** FastAPI + PostgreSQL + LiteLLM gateway + Next.js dashboard, all orchestrated with Docker Compose.

---

## Architecture

```
Your app ──> LiteLLM gateway ──> Provider (OpenAI / Anthropic / Gemini / Ollama)
              (port 4000)  │
                           └── telemetry callback ──> Backend API ──> PostgreSQL
                                                      (port 8000)     (port 5432)
                                                            │
                                                   Next.js dashboard
                                                      (port 3000)
```

| Service    | Port | Purpose                                              |
| ---------- | ---- | ---------------------------------------------------- |
| `frontend` | 3000 | Next.js dashboard UI                                 |
| `backend`  | 8000 | FastAPI analytics API + telemetry ingestion          |
| `litellm`  | 4000 | Unified LLM gateway (the only place providers live)  |
| `postgres` | 5432 | Request/telemetry storage                            |

The backend **never** calls provider SDKs directly — all provider config lives in [`litellm/config.yaml`](litellm/config.yaml).

---

## Prerequisites

- **Docker Desktop** (Compose v2)
- **Node.js 20+** and **pnpm 9** — only for local frontend development
- **[uv](https://docs.astral.sh/uv/)** — only for local backend development
- *(Optional)* **[Ollama](https://ollama.com)** for zero-cost local model testing
- *(Optional)* An API key for OpenAI / Anthropic / Gemini

---

## Quick start

### 1. Configure environment

```powershell
Copy-Item .env.example .env
```

Fill in these required values in `.env`:

| Variable                | How to generate                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------------- |
| `SECRET_KEY`            | `python -c "import secrets; print(secrets.token_urlsafe(32))"`                                |
| `POSTGRES_PASSWORD`     | Any value                                                                                     |
| `LITELLM_MASTER_KEY`    | `python -c "import secrets; print('sk-' + secrets.token_hex(24))"`                            |
| `LITELLM_CALLBACK_TOKEN`| Any random string (shared secret between gateway and backend)                                 |
| `ADMIN_EMAIL`           | Your login email                                                                              |
| `ADMIN_PASSWORD_HASH`   | See below — **must be exactly one bcrypt hash**                                               |
| `OPENAI_API_KEY` etc.   | Optional, per provider you want to use                                                        |

Generate the admin password hash:

```powershell
cd backend
uv run python -c "import bcrypt; print(bcrypt.hashpw(b'YourPasswordHere', bcrypt.gensalt()).decode())"
```

> The output is a single ~60-character string starting with `$2b$12$`. Paste **only that one value** into `ADMIN_PASSWORD_HASH`.

### 2. Start the stack

```powershell
docker compose up --build -d
```

### 3. Verify everything is healthy

```powershell
docker compose ps
```

All four containers should report `(healthy)`:

```
llm-lens-postgres-1   Up (healthy)   0.0.0.0:5432->5432/tcp
llm-lens-backend-1    Up (healthy)   0.0.0.0:8000->8000/tcp
llm-lens-litellm-1    Up (healthy)   0.0.0.0:4000->4000/tcp
llm-lens-frontend-1   Up (healthy)   0.0.0.0:3000->3000/tcp
```

### 4. Open the dashboard

Navigate to **<http://localhost:3000>** — you'll be redirected to `/login`.

Sign in with your `ADMIN_EMAIL` and the plaintext password you hashed above.

| Page                  | Shows                                                        |
| --------------------- | ------------------------------------------------------------ |
| `/`                   | Overview: totals, cost trend, error rate, active models      |
| `/usage`              | Token usage by model / provider                              |
| `/costs`              | Cost breakdown by model / provider / application             |
| `/models`             | Per-model latency (avg, P95), error rate, cost               |
| `/requests`           | Paginated request explorer + detail view                     |
| `/applications`       | Application CRUD + per-app attribution                       |
| `/errors`             | Error counts/rates by provider, model, and category          |

---

## Docker commands

```powershell
# Start everything (detached)
docker compose up -d

# Rebuild images and start
docker compose up --build -d

# Rebuild a single service
docker compose build backend --no-cache

# Recreate a service after changing .env
docker compose up -d --force-recreate backend

# Restart a service after editing mounted files (e.g. litellm/config.yaml)
docker compose restart litellm

# Tail logs
docker compose logs -f backend
docker logs llm-lens-litellm-1 --tail 60

# Status
docker compose ps

# Stop (keeps data)
docker compose down

# Stop and wipe the Postgres volume
docker compose down -v
```

> **Changed `.env`?** Compose bakes env values into containers at creation time. Use `--force-recreate` — a plain `restart` will not pick up changes.

---

## Registering models

The backend **rejects telemetry for unregistered provider/model pairs** (you'll see `telemetry_rejected_unconfigured_model` in the logs). Each model must exist in both places:

**1. Gateway routing** — add to `model_list` in [`litellm/config.yaml`](litellm/config.yaml):

```yaml
- model_name: gemma3:1b
  litellm_params:
    model: ollama/gemma3:1b
    api_base: os.environ/OLLAMA_BASE_URL
```

Then `docker compose restart litellm`.

**2. Backend pricing registry** — insert into the database:

```powershell
docker exec llm-lens-postgres-1 psql -U llm_lens -d llm_lens -c `
  "INSERT INTO providers (name, display_name, enabled) VALUES ('ollama', 'Ollama', true) ON CONFLICT DO NOTHING;"
```

Pricing is per 1M tokens. Local providers use `0` (renders as exactly `$0.00`); unknown pricing stays `NULL` (renders as "Cost unavailable" — never `$0`).

---

## Sending requests

Point any OpenAI-compatible client at `http://localhost:4000` using your `LITELLM_MASTER_KEY` as the bearer token.

### cURL (PowerShell)

> PowerShell aliases `curl` to `Invoke-WebRequest` and mangles inline JSON quoting. **Use `curl.exe` with a JSON file.**

Create `request.json`:

```json
{
  "model": "gpt-4o-mini",
  "messages": [{ "role": "user", "content": "Explain vector databases in one sentence." }]
}
```

Send it:

```powershell
curl.exe http://localhost:4000/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $env:LITELLM_MASTER_KEY" `
  -d "@request.json"
```

### Tag requests to an application

Add a `metadata.application` field to attribute cost per app (untagged requests group under **"unassigned"**):

```json
{
  "model": "gemma3:1b",
  "messages": [{ "role": "user", "content": "Say hi" }],
  "metadata": { "application": "demo-app" }
}
```

### Python

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:4000/v1", api_key="<LITELLM_MASTER_KEY>")

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
print(resp.choices[0].message.content)
```

After any request, refresh <http://localhost:3000/requests> — it appears within a few seconds with provider, model, tokens, cost, and latency.

---

## Backend API

Interactive OpenAPI docs: **<http://localhost:8000/docs>**

All routes are prefixed `/api/v1`. Every route except `/health*` requires an authenticated admin session cookie.

| Endpoint                                                             | Description                        |
| -------------------------------------------------------------------- | ---------------------------------- |
| `GET  /api/v1/health` · `/health/live` · `/health/ready`              | Health checks (no auth)            |
| `POST /api/v1/auth/login` · `/auth/logout` · `GET /auth/session`      | Cookie-based admin auth            |
| `GET  /api/v1/overview`                                              | Dashboard summary metrics          |
| `GET  /api/v1/usage` · `/timeseries` · `/by-model` · `/by-provider`   | Token usage analytics              |
| `GET  /api/v1/costs` · `/timeseries` · `/by-model` · `/by-provider` · `/by-application` | Cost analytics   |
| `GET  /api/v1/models` · `/models/{model_id}`                          | Per-model performance              |
| `GET  /api/v1/requests` · `/requests/{request_id}`                    | Request explorer (paginated)       |
| `GET/POST/PATCH/DELETE /api/v1/applications`                          | Application CRUD                   |
| `GET  /api/v1/errors` · `/by-provider` · `/by-model` · `/by-code`     | Error analytics                    |
| `POST /api/v1/telemetry/events`                                      | Gateway ingestion (service-to-service) |
| `GET  /metrics`                                                      | Prometheus metrics                 |

All analytics endpoints accept `from`, `to`, `provider`, `model`, `application_id`, and `environment` query filters.

### Calling the API directly

Log in to obtain a session cookie, then reuse it:

```powershell
# Login — saves the session cookie
curl.exe -c cookies.txt -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d "@login.json"

# Authenticated request
curl.exe -b cookies.txt "http://localhost:8000/api/v1/overview"
curl.exe -b cookies.txt "http://localhost:8000/api/v1/costs/by-model?from=2026-01-01T00:00:00Z"
```

Where `login.json` contains `{"email": "you@example.com", "password": "YourPasswordHere"}`.

---

## Local development

### Backend

The backend uses [uv](https://docs.astral.sh/uv/), which manages its own Python 3.12 virtual environment.

```powershell
cd backend
uv sync
```

**Activating the virtual environment** (optional — `uv run` works without it):

```powershell
# PowerShell blocks venv scripts by default; bypass for this session only
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
```

> This affects only the current terminal — re-run it in each new window. You do **not** need to activate the venv if you prefix commands with `uv run`.

Run the dev server (requires Postgres — start it with `docker compose up -d postgres`):

```powershell
uv run alembic upgrade head        # apply migrations
uv run uvicorn app.main:app --reload --port 8000
```

Quality gates:

```powershell
uv run ruff check .                # lint
uv run mypy app                    # type-check
uv run pytest                      # tests
```

> Integration tests requiring PostgreSQL skip automatically when no database is reachable.

### Frontend

```powershell
cd frontend
pnpm install
pnpm dev                           # http://localhost:3000
```

Quality gates:

```powershell
pnpm lint
pnpm typecheck
pnpm test                          # vitest unit tests
pnpm test:e2e                      # playwright (needs a running dev server)
pnpm build
```

> If pnpm is blocked by PowerShell's execution policy, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force` first.

---

## Configuration reference

Key `.env` variables:

| Variable                 | Default                  | Description                                            |
| ------------------------ | ------------------------ | ------------------------------------------------------ |
| `APP_ENV`                | `development`            | Environment name                                       |
| `SECRET_KEY`             | —                        | Session signing key                                    |
| `DATABASE_URL`           | —                        | Only used when running the backend outside Docker      |
| `CORS_ALLOW_ORIGINS`     | `http://localhost:3000`  | Comma-separated origin allowlist                       |
| `ADMIN_EMAIL`            | —                        | Admin login email                                      |
| `ADMIN_PASSWORD_HASH`    | —                        | Single bcrypt hash                                     |
| `LITELLM_MASTER_KEY`     | —                        | Bearer token for the gateway                           |
| `LITELLM_CALLBACK_TOKEN` | —                        | Shared secret for telemetry ingestion                  |
| `OLLAMA_BASE_URL`        | `http://host.docker.internal:11434` | Local Ollama endpoint                       |
| `STORE_PROMPTS`          | `false`                  | **Keep `false`** unless you explicitly need content    |
| `STORE_RESPONSES`        | `false`                  | **Keep `false`** unless you explicitly need content    |
| `REQUEST_RETENTION_DAYS` | `90`                     | Retention window                                       |

---

## Privacy & cost semantics

- **No content by default.** Prompts and responses are never persisted unless `STORE_PROMPTS` / `STORE_RESPONSES` are explicitly enabled. The request detail view shows metadata only.
- **Cost is never guessed.** Three distinct states:
  - **Calculated** — pricing is known → exact cost
  - **`$0.00`** — zero-cost provider (e.g. local Ollama) → exactly zero
  - **"Cost unavailable"** — pricing unknown → `NULL`, never displayed as `$0`

---

## Troubleshooting

| Symptom                                                        | Fix                                                                                             |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `401` on login despite correct password                        | `ADMIN_PASSWORD_HASH` must be exactly one bcrypt hash. Then `docker compose up -d --force-recreate backend`. |
| Request succeeds at the gateway but never appears in the UI    | Check `docker compose logs backend` for `telemetry_rejected_unconfigured_model` — register the provider/model. |
| `Invalid JSON payload` from cURL                               | Use `curl.exe` (not `curl`) with `-d "@file.json"` — PowerShell mangles inline JSON.             |
| `RateLimitError: You have no credits remaining`                | Provider-side billing issue. Add credits, or test with local Ollama.                             |
| `running scripts is disabled on this system`                   | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force`                              |
| Postgres unhealthy / `find: unknown user postgres`             | Corrupted image layer: `docker rmi postgres:16-alpine -f`, then `docker compose pull postgres`.  |
| `.env` changes not taking effect                               | `docker compose up -d --force-recreate <service>` — `restart` alone won't reload env.            |

---

## Project structure

```
llm-lens/
├── backend/          FastAPI app, SQLAlchemy models, Alembic migrations, tests
├── frontend/         Next.js 15 dashboard (App Router, TanStack Query, shadcn/ui)
├── litellm/          Gateway config + telemetry callback
├── specs/            Feature specification, plan, and task breakdown
├── docs/             Additional documentation
└── docker-compose.yml
```
