"""Models analytics pages (T235) — Jinja port of frontend/src/app/models/*."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import RangeFilterDep
from app.db.session import get_db
from app.services.analytics_service import get_model_summaries, get_model_summary
from app.services.project_service import list_projects
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])


@router.get("/models")
async def models_list_page(
    request: Request, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> object:
    rows = get_model_summaries(db, filters)
    context = {"rows": rows, "projects": list_projects(db), "filters": filters}
    template = "models/_results.html" if request.headers.get("HX-Request") else "models/list.html"
    return templates.TemplateResponse(request, template, context)


@router.get("/models/{model_id}")
async def model_detail_page(
    request: Request, model_id: str, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> object:
    row = get_model_summary(db, filters, model_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No requests for model '{model_id}'",
        )
    context = {
        "row": row,
        "model_id": model_id,
        "projects": list_projects(db),
        "filters": filters,
    }
    return templates.TemplateResponse(request, "models/detail.html", context)
