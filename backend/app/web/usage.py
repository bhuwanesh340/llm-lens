"""Usage analytics page (T233) — Jinja port of frontend/src/app/usage/page.tsx."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import RangeFilterDep
from app.db.session import get_db
from app.services.project_service import list_projects
from app.services.usage_service import get_usage_by_model, get_usage_by_provider, get_usage_summary
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])

_VIEWS = ("model", "provider")


@router.get("/usage")
async def usage_page(
    request: Request,
    filters: RangeFilterDep,
    view: str = Query("model"),
    db: Session = Depends(get_db),
) -> object:
    view = view if view in _VIEWS else "model"
    summary = get_usage_summary(db, filters)
    if view == "model":
        breakdown = get_usage_by_model(db, filters)
    else:
        breakdown = get_usage_by_provider(db, filters)
    context = {
        "summary": summary,
        "breakdown": breakdown,
        "view": view,
        "projects": list_projects(db),
        "filters": filters,
    }
    template = "usage/_results.html" if request.headers.get("HX-Request") else "usage/page.html"
    return templates.TemplateResponse(request, template, context)
