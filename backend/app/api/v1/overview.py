"""`GET /api/v1/overview` (T041, US2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminSession, RangeFilterDep
from app.db.session import get_db
from app.schemas.analytics import OverviewResponse
from app.services.analytics_service import get_overview

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("", response_model=OverviewResponse)
async def overview(
    _: AdminSession,
    filters: RangeFilterDep,
    db: Session = Depends(get_db),
) -> OverviewResponse:
    result = get_overview(db, filters)
    return OverviewResponse.model_validate(result)
