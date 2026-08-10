"""Shared filter-application logic for the `llm_requests` table, used by
`analytics_service.py` and `usage_service.py` (Phase 4+).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Select

from app.api.deps import RangeFilters
from app.db.models.request import LLMRequest


class InvalidFilterError(ValueError):
    """Raised for a malformed or logically invalid filter (→ HTTP 400)."""


def apply_request_filters(stmt: Select[Any], filters: RangeFilters) -> Select[Any]:
    """Apply the common time-range/entity filters to a `LLMRequest` select."""

    if (
        filters.date_from is not None
        and filters.date_to is not None
        and filters.date_from > filters.date_to
    ):
        raise InvalidFilterError("'from' must not be after 'to'")

    conditions = []
    if filters.date_from is not None:
        conditions.append(LLMRequest.created_at >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(LLMRequest.created_at <= filters.date_to)
    if filters.provider is not None:
        conditions.append(LLMRequest.provider == filters.provider)
    if filters.model is not None:
        conditions.append(LLMRequest.model == filters.model)
    if filters.environment is not None:
        conditions.append(LLMRequest.environment == filters.environment)
    if filters.application_id is not None:
        if filters.application_id == "unassigned":
            conditions.append(LLMRequest.application_id.is_(None))
        else:
            try:
                app_uuid = uuid.UUID(filters.application_id)
            except ValueError as exc:
                raise InvalidFilterError(
                    "'application_id' must be a valid UUID or 'unassigned'"
                ) from exc
            conditions.append(LLMRequest.application_id == app_uuid)

    if conditions:
        stmt = stmt.where(*conditions)
    return stmt
