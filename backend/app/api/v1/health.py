"""Health endpoints (T018) — `/api/v1/health*`.

Exempt from admin-session auth per contracts/api.md Authentication section
("Unauthenticated requests to any `/api/v1/*` route other than `/health*`
MUST return 401").
"""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from app.db.session import get_engine

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: str = "ok"


class ReadinessResponse(BaseModel):
    status: str
    database: str


class HealthResponse(BaseModel):
    status: str
    database: str


@router.get("/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    """Process liveness only — never touches the database."""

    return LivenessResponse(status="ok")


def _check_database() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - readiness probe must not raise
        return False


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(response_status: int = status.HTTP_200_OK) -> ReadinessResponse:
    """Dependency readiness (DB reachable)."""

    db_ok = _check_database()
    return ReadinessResponse(
        status="ok" if db_ok else "unavailable", database="ok" if db_ok else "unreachable"
    )


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Overall liveness+readiness summary."""

    db_ok = _check_database()
    return HealthResponse(
        status="ok" if db_ok else "degraded", database="ok" if db_ok else "unreachable"
    )
