"""Request Explorer pages (T236) — Jinja port of frontend/src/app/requests/*."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import PaginationDep, RangeFilterDep
from app.db.session import get_db
from app.services.project_service import list_projects
from app.services.request_service import get_request_by_request_id, list_requests
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])


@router.get("/requests")
async def requests_list_page(
    request: Request,
    filters: RangeFilterDep,
    pagination: PaginationDep,
    db: Session = Depends(get_db),
) -> object:
    result = list_requests(db, filters, pagination)
    context = {
        "result": result,
        "projects": list_projects(db),
        "filters": filters,
    }
    is_htmx = request.headers.get("HX-Request")
    template = "requests/_results.html" if is_htmx else "requests/list.html"
    return templates.TemplateResponse(request, template, context)


@router.get("/requests/{request_id}")
async def request_detail_page(
    request: Request, request_id: str, db: Session = Depends(get_db)
) -> object:
    item = get_request_by_request_id(db, request_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No request '{request_id}'"
        )
    return templates.TemplateResponse(request, "requests/detail.html", {"item": item})
