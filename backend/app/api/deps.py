"""Shared API dependencies for Phase 4+ endpoints: pagination, range/entity
filters, and the admin-session auth dependency alias.

Not tied to a single task ID — used by overview.py/usage.py/costs.py/
models.py/requests.py/applications.py/errors.py (T041-T062).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Query

from app.core.security import require_admin_session

# Applied as a router-level dependency on every non-health, non-auth,
# non-telemetry router so unauthenticated requests get 401 (FR-023).
AdminSession = Annotated[str, Depends(require_admin_session)]


@dataclass(frozen=True)
class RangeFilters:
    """Common time-range + entity filters shared by analytics endpoints."""

    date_from: datetime | None
    date_to: datetime | None
    provider: str | None
    model: str | None
    project_id: str | None
    environment: str | None


def get_range_filters(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None, alias="to"),
    provider: str | None = Query(None),
    model: str | None = Query(None),
    project_id: str | None = Query(None),
    environment: str | None = Query(None),
) -> RangeFilters:
    return RangeFilters(
        date_from=from_,
        date_to=to,
        provider=provider,
        model=model,
        project_id=project_id,
        environment=environment,
    )


RangeFilterDep = Annotated[RangeFilters, Depends(get_range_filters)]


@dataclass(frozen=True)
class PaginationParams:
    page: int
    page_size: int
    sort: str | None
    order: str


def get_pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str | None = Query(None),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size, sort=sort, order=order)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination)]
