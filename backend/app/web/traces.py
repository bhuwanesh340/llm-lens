"""Trace browsing UI (T227, T229, T230) — feature 003 Phase 3.

Server-rendered with HTMX-powered filtering (the filter form triggers a
partial swap of the results table, no full page reload) instead of a
React SPA (FR-219).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.project_service import list_projects
from app.services.trace_query_service import get_trace_detail, list_traces
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


@router.get("/traces")
async def traces_list_page(
    request: Request,
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> object:
    result = list_traces(
        db,
        project_id=_parse_uuid(project_id),
        status=status or None,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=20,
    )
    context = {
        "result": result,
        "projects": list_projects(db),
        "filters": {"project_id": project_id, "status": status},
        "has_any_traces": result.total > 0,
    }
    template = "traces/_results.html" if request.headers.get("HX-Request") else "traces/list.html"
    return templates.TemplateResponse(request, template, context)


@router.get("/traces/{trace_id}")
async def trace_detail_page(
    request: Request, trace_id: str, db: Session = Depends(get_db)
) -> object:
    detail = get_trace_detail(db, trace_id)
    settings = get_settings()
    show_content = settings.store_prompts or settings.store_responses
    return templates.TemplateResponse(
        request,
        "traces/detail.html",
        {"detail": detail, "trace_id": trace_id, "show_content": show_content},
    )
