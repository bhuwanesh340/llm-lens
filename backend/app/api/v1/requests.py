"""`GET /api/v1/requests`, `/requests/{request_id}` — Request Explorer
(T051-T052, US3).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AdminSession, PaginationDep, RangeFilterDep
from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.requests import RequestDetail, RequestListItem
from app.services.request_service import get_request_by_request_id, list_requests

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=Page[RequestListItem])
async def requests_list(
    _: AdminSession,
    filters: RangeFilterDep,
    pagination: PaginationDep,
    db: Session = Depends(get_db),
) -> Page[RequestListItem]:
    return list_requests(db, filters, pagination)


@router.get("/{request_id}", response_model=RequestDetail)
async def request_detail(
    request_id: str,
    _: AdminSession,
    db: Session = Depends(get_db),
) -> RequestDetail:
    record = get_request_by_request_id(db, request_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REQUEST_NOT_FOUND",
                "message": f"No request found with request_id '{request_id}'",
            },
        )
    return RequestDetail(
        id=record.id,
        request_id=record.request_id,
        created_at=record.created_at,
        completed_at=record.completed_at,
        provider=record.provider,
        model=record.model,
        project_id=record.project_id,
        environment=record.environment,
        status=record.status,
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        total_tokens=record.total_tokens,
        input_cost=record.input_cost,
        output_cost=record.output_cost,
        total_cost=record.total_cost,
        latency_ms=record.latency_ms,
        ttft_ms=record.ttft_ms,
        api_key_id=record.api_key_id,
        error_type=record.error_type,
        error_code=record.error_code,
        error_message=record.error_message,
        metadata=record.metadata_,
    )
