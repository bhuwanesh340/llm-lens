"""Server-rendered UI routers (Jinja2 + HTMX), mounted at the app root (no
`/api/v1` prefix — distinct from the JSON API in `app.api`)."""

from __future__ import annotations

from fastapi import APIRouter

from app.web import auth, costs, errors, models, overview, projects, requests, traces, usage

web_router = APIRouter()
web_router.include_router(auth.router)
web_router.include_router(overview.router)
web_router.include_router(usage.router)
web_router.include_router(costs.router)
web_router.include_router(models.router)
web_router.include_router(requests.router)
web_router.include_router(projects.router)
web_router.include_router(errors.router)
web_router.include_router(traces.router)

__all__ = ["web_router"]
