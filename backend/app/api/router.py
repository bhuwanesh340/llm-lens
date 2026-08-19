"""API v1 router mounting (T015)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    api_keys,
    auth,
    costs,
    errors,
    health,
    models,
    overview,
    projects,
    requests,
    telemetry,
    traces,
    usage,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(telemetry.router)
api_router.include_router(overview.router)
api_router.include_router(usage.router)
api_router.include_router(costs.router)
api_router.include_router(models.router)
api_router.include_router(requests.router)
api_router.include_router(projects.router)
api_router.include_router(api_keys.router)
api_router.include_router(traces.router)
api_router.include_router(errors.router)
