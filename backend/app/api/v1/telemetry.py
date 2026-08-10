"""Telemetry ingestion webhook (T031/T032).

Receives raw telemetry events from LiteLLM's custom callback
(`litellm/custom_callbacks.py`) after each completed request (success or
failure) and hands them to the telemetry collector. This is a
service-to-service endpoint authenticated via a shared token
(`LITELLM_CALLBACK_TOKEN`), NOT the admin browser session — it is not part
of the dashboard's public contract (contracts/api.md).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.telemetry.collector import (
    DuplicateRequestIdError,
    UnconfiguredModelError,
    collect_telemetry_event,
)
from app.telemetry.events import RawTelemetryEvent

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def _verify_callback_token(request: Request) -> None:
    settings = get_settings()
    token = request.headers.get("X-Internal-Token")
    if not token or token != settings.litellm_callback_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid callback token"
        )


@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_verify_callback_token)],
)
async def ingest_telemetry_event(
    event: RawTelemetryEvent, db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        record = collect_telemetry_event(db, event)
    except UnconfiguredModelError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except DuplicateRequestIdError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"request_id": record.request_id, "status": "recorded"}
