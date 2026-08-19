"""Server-rendered UI routers (Jinja2 + HTMX), mounted at the app root (no
`/api/v1` prefix — distinct from the JSON API in `app.api`)."""

from __future__ import annotations

from fastapi import APIRouter

from app.web import auth, traces

web_router = APIRouter()
web_router.include_router(auth.router)
web_router.include_router(traces.router)

__all__ = ["web_router"]
