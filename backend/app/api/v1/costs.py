"""`GET /api/v1/costs*` endpoints (T043, US2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminSession, RangeFilterDep
from app.db.session import get_db
from app.schemas.analytics import CostBreakdownItem, CostTimeseriesItem
from app.services.analytics_service import (
    get_costs_by_model,
    get_costs_by_project,
    get_costs_by_provider,
    get_costs_timeseries,
)

router = APIRouter(prefix="/costs", tags=["costs"])


@router.get("", response_model=list[CostBreakdownItem])
async def costs(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[CostBreakdownItem]:
    return [CostBreakdownItem.model_validate(row) for row in get_costs_by_model(db, filters)]


@router.get("/timeseries", response_model=list[CostTimeseriesItem])
async def costs_timeseries(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[CostTimeseriesItem]:
    return [CostTimeseriesItem.model_validate(row) for row in get_costs_timeseries(db, filters)]


@router.get("/by-model", response_model=list[CostBreakdownItem])
async def costs_by_model(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[CostBreakdownItem]:
    return [CostBreakdownItem.model_validate(row) for row in get_costs_by_model(db, filters)]


@router.get("/by-provider", response_model=list[CostBreakdownItem])
async def costs_by_provider(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[CostBreakdownItem]:
    return [CostBreakdownItem.model_validate(row) for row in get_costs_by_provider(db, filters)]


@router.get("/by-project", response_model=list[CostBreakdownItem])
async def costs_by_project(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[CostBreakdownItem]:
    return [CostBreakdownItem.model_validate(row) for row in get_costs_by_project(db, filters)]
