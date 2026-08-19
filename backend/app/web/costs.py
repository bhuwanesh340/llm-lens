"""Costs analytics page (T234) — Jinja port of frontend/src/app/costs/page.tsx."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import RangeFilterDep
from app.db.session import get_db
from app.services.analytics_service import (
    get_costs_by_model,
    get_costs_by_project,
    get_costs_by_provider,
    get_costs_timeseries,
)
from app.services.project_service import list_projects
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])

_VIEWS = ("model", "provider", "project")
_BREAKDOWNS = {
    "model": get_costs_by_model,
    "provider": get_costs_by_provider,
    "project": get_costs_by_project,
}


@router.get("/costs")
async def costs_page(
    request: Request,
    filters: RangeFilterDep,
    view: str = Query("model"),
    db: Session = Depends(get_db),
) -> object:
    view = view if view in _VIEWS else "model"
    timeseries = get_costs_timeseries(db, filters)
    max_cost = max((float(p.total_cost) for p in timeseries if p.total_cost), default=0.0)
    breakdown = _BREAKDOWNS[view](db, filters)
    projects = list_projects(db)
    project_names = {str(project.id): project.name for project in projects}
    context = {
        "timeseries": timeseries,
        "max_cost": max_cost or 1.0,
        "breakdown": breakdown,
        "view": view,
        "project_names": project_names,
        "projects": projects,
        "filters": filters,
    }
    template = "costs/_results.html" if request.headers.get("HX-Request") else "costs/page.html"
    return templates.TemplateResponse(request, template, context)
