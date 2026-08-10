"""Usage aggregation service: token/request counts over `llm_requests`
(T040).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import RangeFilters
from app.db.models.request import LLMRequest
from app.services.query_filters import apply_request_filters

_UNASSIGNED = "unassigned"


@dataclass(frozen=True)
class UsageSummary:
    total_requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    avg_tokens_per_request: float


def get_usage_summary(db: Session, filters: RangeFilters) -> UsageSummary:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()
    row = db.execute(
        select(
            func.count(subq.c.id),
            func.sum(subq.c.input_tokens),
            func.sum(subq.c.output_tokens),
            func.sum(subq.c.total_tokens),
        )
    ).one()
    total_requests, input_tokens, output_tokens, total_tokens = row
    total_requests = total_requests or 0
    total_tokens = total_tokens or 0
    return UsageSummary(
        total_requests=total_requests,
        input_tokens=input_tokens or 0,
        output_tokens=output_tokens or 0,
        total_tokens=total_tokens,
        avg_tokens_per_request=(total_tokens / total_requests) if total_requests else 0.0,
    )


@dataclass(frozen=True)
class UsageTimeseriesPoint:
    date: datetime
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int


def get_usage_timeseries(db: Session, filters: RangeFilters) -> list[UsageTimeseriesPoint]:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()
    day = func.date_trunc("day", subq.c.created_at)

    rows = db.execute(
        select(
            day,
            func.sum(subq.c.input_tokens),
            func.sum(subq.c.output_tokens),
            func.sum(subq.c.total_tokens),
            func.count(subq.c.id),
        )
        .group_by(day)
        .order_by(day)
    ).all()

    return [
        UsageTimeseriesPoint(
            date=bucket,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
            total_tokens=total_tokens or 0,
            request_count=count,
        )
        for bucket, input_tokens, output_tokens, total_tokens, count in rows
    ]


@dataclass(frozen=True)
class UsageBreakdownRow:
    key: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int
    avg_tokens_per_request: float


def _usage_breakdown_by(
    db: Session, filters: RangeFilters, group_col: str
) -> list[UsageBreakdownRow]:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()
    group_expr = getattr(subq.c, group_col)

    rows = db.execute(
        select(
            group_expr,
            func.sum(subq.c.input_tokens),
            func.sum(subq.c.output_tokens),
            func.sum(subq.c.total_tokens),
            func.count(subq.c.id),
        )
        .group_by(group_expr)
        .order_by(group_expr)
    ).all()

    return [
        UsageBreakdownRow(
            key=str(key) if key is not None else _UNASSIGNED,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
            total_tokens=total_tokens or 0,
            request_count=count,
            avg_tokens_per_request=((total_tokens or 0) / count) if count else 0.0,
        )
        for key, input_tokens, output_tokens, total_tokens, count in rows
    ]


def get_usage_by_model(db: Session, filters: RangeFilters) -> list[UsageBreakdownRow]:
    return _usage_breakdown_by(db, filters, "model")


def get_usage_by_provider(db: Session, filters: RangeFilters) -> list[UsageBreakdownRow]:
    return _usage_breakdown_by(db, filters, "provider")
