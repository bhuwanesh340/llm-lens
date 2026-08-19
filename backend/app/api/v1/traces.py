"""SDK trace/span ingestion endpoint (T210) — feature 003 Phase 1.

Authenticated via a project API key or the shared gateway token + project
name (`resolve_trace_ingest_project`), NOT the admin browser session — this
is the SDK's ingestion path, analogous to how `telemetry.py` is the
LiteLLM gateway's ingestion path.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import resolve_trace_ingest_project
from app.db.session import get_db
from app.schemas.traces import TraceIngestPayload
from app.services.trace_service import ingest_trace as ingest_trace_service

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_trace(
    payload: TraceIngestPayload,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    project_id = resolve_trace_ingest_project(request, payload.project, db)
    trace = ingest_trace_service(db, project_id, payload)
    return {"trace_id": trace.id, "status": "recorded"}
