"""Overview dashboard page (T232) — Jinja port of frontend/src/app/page.tsx."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import RangeFilterDep
from app.db.session import get_db
from app.services.analytics_service import get_costs_timeseries, get_overview
from app.services.project_service import list_projects
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])


@router.get("/")
async def overview_page(
    request: Request, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> object:
    overview = get_overview(db, filters)
    timeseries = get_costs_timeseries(db, filters)
    max_cost = max((float(p.total_cost) for p in timeseries if p.total_cost), default=0.0)
    context = {
        "overview": overview,
        "timeseries": timeseries,
        "max_cost": max_cost or 1.0,
        "projects": list_projects(db),
        "filters": filters,
    }
    template = "_overview_results.html" if request.headers.get("HX-Request") else "overview.html"
    return templates.TemplateResponse(request, template, context)
