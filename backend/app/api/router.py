"""API v1 router mounting (T015)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import health, telemetry

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(telemetry.router)
