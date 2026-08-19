"""Errors analytics page (T238) — Jinja port of frontend/src/app/errors/page.tsx."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import RangeFilterDep
from app.db.session import get_db
from app.services.analytics_service import (
    get_errors_by_code,
    get_errors_by_model,
    get_errors_by_provider,
    get_errors_summary,
)
from app.services.project_service import list_projects
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])

_VIEWS = ("provider", "model", "code")
_BREAKDOWNS = {
    "provider": get_errors_by_provider,
    "model": get_errors_by_model,
    "code": get_errors_by_code,
}


@router.get("/errors")
async def errors_page(
    request: Request,
    filters: RangeFilterDep,
    view: str = Query("provider"),
    db: Session = Depends(get_db),
) -> object:
    view = view if view in _VIEWS else "provider"
    summary = get_errors_summary(db, filters)
    breakdown = _BREAKDOWNS[view](db, filters)
    context = {
        "summary": summary,
        "breakdown": breakdown,
        "view": view,
        "projects": list_projects(db),
        "filters": filters,
    }
    template = "errors/_results.html" if request.headers.get("HX-Request") else "errors/page.html"
    return templates.TemplateResponse(request, template, context)
