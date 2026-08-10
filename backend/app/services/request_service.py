"""Request Explorer query service (T051-T052, US3)."""

from __future__ import annotations

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, RangeFilters
from app.db.models.request import LLMRequest
from app.schemas.common import Page, PageMeta
from app.schemas.requests import RequestListItem
from app.services.query_filters import InvalidFilterError, apply_request_filters

_SORTABLE_COLUMNS = {
    "created_at": LLMRequest.created_at,
    "total_cost": LLMRequest.total_cost,
    "latency_ms": LLMRequest.latency_ms,
    "total_tokens": LLMRequest.total_tokens,
}


def list_requests(
    db: Session, filters: RangeFilters, pagination: PaginationParams
) -> Page[RequestListItem]:
    stmt = apply_request_filters(select(LLMRequest), filters)

    sort_key = pagination.sort or "created_at"
    sort_column = _SORTABLE_COLUMNS.get(sort_key)
    if sort_column is None:
        raise InvalidFilterError(
            f"'sort' must be one of {sorted(_SORTABLE_COLUMNS)}, got '{sort_key}'"
        )
    order_fn = asc if pagination.order == "asc" else desc
    stmt = stmt.order_by(order_fn(sort_column))

    total_items = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    offset = (pagination.page - 1) * pagination.page_size
    rows = db.execute(stmt.offset(offset).limit(pagination.page_size)).scalars().all()

    total_pages = (
        (total_items + pagination.page_size - 1) // pagination.page_size if total_items else 0
    )
    return Page[RequestListItem](
        items=[RequestListItem.model_validate(row) for row in rows],
        meta=PageMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


def get_request_by_request_id(db: Session, request_id: str) -> LLMRequest | None:
    stmt = select(LLMRequest).where(LLMRequest.request_id == request_id)
    return db.execute(stmt).scalar_one_or_none()
