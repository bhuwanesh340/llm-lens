"""`GET /api/v1/errors*` endpoints (T062, US5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminSession, RangeFilterDep
from app.db.session import get_db
from app.schemas.analytics import ErrorBreakdownItem, ErrorsSummaryResponse
from app.services.analytics_service import (
    get_errors_by_code,
    get_errors_by_model,
    get_errors_by_provider,
    get_errors_summary,
)

router = APIRouter(prefix="/errors", tags=["errors"])


@router.get("", response_model=ErrorsSummaryResponse)
async def errors(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> ErrorsSummaryResponse:
    return ErrorsSummaryResponse.model_validate(get_errors_summary(db, filters))


@router.get("/by-provider", response_model=list[ErrorBreakdownItem])
async def errors_by_provider(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[ErrorBreakdownItem]:
    return [ErrorBreakdownItem.model_validate(row) for row in get_errors_by_provider(db, filters)]


@router.get("/by-model", response_model=list[ErrorBreakdownItem])
async def errors_by_model(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[ErrorBreakdownItem]:
    return [ErrorBreakdownItem.model_validate(row) for row in get_errors_by_model(db, filters)]


@router.get("/by-code", response_model=list[ErrorBreakdownItem])
async def errors_by_code(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[ErrorBreakdownItem]:
    return [ErrorBreakdownItem.model_validate(row) for row in get_errors_by_code(db, filters)]
