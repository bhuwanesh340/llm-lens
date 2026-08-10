"""`GET /api/v1/usage*` endpoints (T042, US2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminSession, RangeFilterDep
from app.db.session import get_db
from app.schemas.analytics import UsageBreakdownItem, UsageSummaryResponse, UsageTimeseriesItem
from app.services.usage_service import (
    get_usage_by_model,
    get_usage_by_provider,
    get_usage_summary,
    get_usage_timeseries,
)

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageSummaryResponse)
async def usage(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> UsageSummaryResponse:
    return UsageSummaryResponse.model_validate(get_usage_summary(db, filters))


@router.get("/timeseries", response_model=list[UsageTimeseriesItem])
async def usage_timeseries(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[UsageTimeseriesItem]:
    return [UsageTimeseriesItem.model_validate(row) for row in get_usage_timeseries(db, filters)]


@router.get("/by-model", response_model=list[UsageBreakdownItem])
async def usage_by_model(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[UsageBreakdownItem]:
    return [UsageBreakdownItem.model_validate(row) for row in get_usage_by_model(db, filters)]


@router.get("/by-provider", response_model=list[UsageBreakdownItem])
async def usage_by_provider(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[UsageBreakdownItem]:
    return [UsageBreakdownItem.model_validate(row) for row in get_usage_by_provider(db, filters)]
