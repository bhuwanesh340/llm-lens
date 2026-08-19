"""Shared API dependencies for Phase 4+ endpoints: pagination, range/entity
filters, and the admin-session auth dependency alias.

Not tied to a single task ID — used by overview.py/usage.py/costs.py/
models.py/requests.py/applications.py/errors.py (T041-T062).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import require_admin_session
from app.services.api_key_service import verify_api_key
from app.services.project_service import InvalidProjectNameError, resolve_or_create_project

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


def resolve_trace_ingest_project(
    request: Request, project_name: str | None, db: Session
) -> uuid.UUID | None:
    """FR-214/FR-216/FR-217: authenticate an SDK ingest call.

    Three supported paths, in precedence order:
    1. Project API key (`Authorization: Bearer llk_...`) — precise attribution.
    2. Shared gateway token (same `LITELLM_CALLBACK_TOKEN` feature 002's
       gateway path uses) + a `project` name in the payload — auto-resolved/
       created identically to gateway traces.
    3. No `Authorization` header at all + a `project` name in the payload —
       the SDK's documented zero-config quickstart (`configure(project=...)`
       with no key/token). Treated as anonymous-but-named, not "invalid", so
       it is allowed rather than rejected; this matches the trust model of a
       single-admin, self-hosted deployment.

    Any *present* Bearer token that doesn't match one of the above is
    rejected as 401 (FR-218), as is a request with neither a valid token nor
    a project name to fall back on.
    """

    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        if project_name:
            try:
                return resolve_or_create_project(db, project_name).id
            except InvalidProjectNameError:
                return None
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    token = auth_header.removeprefix("Bearer ").strip()

    project_id = verify_api_key(db, token)
    if project_id is not None:
        return project_id

    if project_name and token == get_settings().litellm_callback_token:
        try:
            return resolve_or_create_project(db, project_name).id
        except InvalidProjectNameError:
            return None

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")



PaginationDep = Annotated[PaginationParams, Depends(get_pagination)]
