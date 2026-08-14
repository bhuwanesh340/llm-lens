"""Analytics aggregation service: overview, cost breakdowns, and error
breakdowns over `llm_requests` (T039, extended by T061 for errors).

Cost null-handling (constitution Principle III / data-model.md): `SUM()`
over a nullable column ignores NULLs in SQL, so a plain sum would silently
under-report without signaling that some rows had unknown pricing. Every
aggregate here therefore also returns an `unknown_cost_count` so callers
(and the frontend) can render "some costs unavailable" instead of a
misleadingly precise total.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.api.deps import RangeFilters
from app.db.models.request import LLMRequest
from app.services.query_filters import apply_request_filters

_UNASSIGNED = "unassigned"


@dataclass(frozen=True)
class OverviewResult:
    total_requests: int
    total_cost: Decimal | None
    unknown_cost_count: int
    total_tokens: int
    avg_latency_ms: float | None
    error_rate: float
    active_models: int


def get_overview(db: Session, filters: RangeFilters) -> OverviewResult:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()

    row = db.execute(
        select(
            func.count(subq.c.id),
            func.sum(subq.c.total_cost),
            func.sum(case((subq.c.total_cost.is_(None), 1), else_=0)),
            func.sum(subq.c.total_tokens),
            func.avg(subq.c.latency_ms),
            func.sum(case((subq.c.status == "error", 1), else_=0)),
            func.count(func.distinct(subq.c.model)),
        )
    ).one()

    (
        total_requests,
        total_cost,
        unknown_cost_count,
        total_tokens,
        avg_latency,
        error_count,
        active_models,
    ) = row
    total_requests = total_requests or 0
    error_count = error_count or 0

    return OverviewResult(
        total_requests=total_requests,
        total_cost=total_cost,
        unknown_cost_count=unknown_cost_count or 0,
        total_tokens=total_tokens or 0,
        avg_latency_ms=float(avg_latency) if avg_latency is not None else None,
        error_rate=(error_count / total_requests) if total_requests else 0.0,
        active_models=active_models or 0,
    )


@dataclass(frozen=True)
class CostBreakdownRow:
    key: str
    total_cost: Decimal | None
    unknown_cost_count: int
    request_count: int


def _cost_breakdown_by(
    db: Session, filters: RangeFilters, group_col: str
) -> list[CostBreakdownRow]:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()
    group_expr = getattr(subq.c, group_col)

    rows = db.execute(
        select(
            group_expr,
            func.sum(subq.c.total_cost),
            func.sum(case((subq.c.total_cost.is_(None), 1), else_=0)),
            func.count(subq.c.id),
        )
        .group_by(group_expr)
        .order_by(group_expr)
    ).all()

    return [
        CostBreakdownRow(
            key=str(key) if key is not None else _UNASSIGNED,
            total_cost=total_cost,
            unknown_cost_count=unknown_count or 0,
            request_count=request_count,
        )
        for key, total_cost, unknown_count, request_count in rows
    ]


def get_costs_by_model(db: Session, filters: RangeFilters) -> list[CostBreakdownRow]:
    return _cost_breakdown_by(db, filters, "model")


def get_costs_by_provider(db: Session, filters: RangeFilters) -> list[CostBreakdownRow]:
    return _cost_breakdown_by(db, filters, "provider")


def get_costs_by_project(db: Session, filters: RangeFilters) -> list[CostBreakdownRow]:
    return _cost_breakdown_by(db, filters, "project_id")


@dataclass(frozen=True)
class CostTimeseriesPoint:
    date: datetime
    total_cost: Decimal | None
    unknown_cost_count: int
    request_count: int


def get_costs_timeseries(db: Session, filters: RangeFilters) -> list[CostTimeseriesPoint]:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()
    day = func.date_trunc("day", subq.c.created_at)

    rows = db.execute(
        select(
            day,
            func.sum(subq.c.total_cost),
            func.sum(case((subq.c.total_cost.is_(None), 1), else_=0)),
            func.count(subq.c.id),
        )
        .group_by(day)
        .order_by(day)
    ).all()

    return [
        CostTimeseriesPoint(
            date=bucket,
            total_cost=total_cost,
            unknown_cost_count=unknown_count or 0,
            request_count=count,
        )
        for bucket, total_cost, unknown_count, count in rows
    ]


@dataclass(frozen=True)
class ErrorBreakdownRow:
    key: str
    error_count: int
    total_count: int
    error_rate: float


def _error_breakdown_by(
    stmt: Select[Any], group_col_name: str, db: Session
) -> list[ErrorBreakdownRow]:
    subq = stmt.subquery()
    group_expr = getattr(subq.c, group_col_name)

    rows = db.execute(
        select(
            group_expr,
            func.sum(case((subq.c.status == "error", 1), else_=0)),
            func.count(subq.c.id),
        )
        .group_by(group_expr)
        .order_by(group_expr)
    ).all()

    return [
        ErrorBreakdownRow(
            key=str(key) if key is not None else _UNASSIGNED,
            error_count=error_count or 0,
            total_count=total_count,
            error_rate=((error_count or 0) / total_count) if total_count else 0.0,
        )
        for key, error_count, total_count in rows
    ]


@dataclass(frozen=True)
class ErrorsSummary:
    total_requests: int
    error_count: int
    error_rate: float


def get_errors_summary(db: Session, filters: RangeFilters) -> ErrorsSummary:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()
    row = db.execute(
        select(
            func.count(subq.c.id),
            func.sum(case((subq.c.status == "error", 1), else_=0)),
        )
    ).one()
    total_requests, error_count = row
    total_requests = total_requests or 0
    error_count = error_count or 0
    return ErrorsSummary(
        total_requests=total_requests,
        error_count=error_count,
        error_rate=(error_count / total_requests) if total_requests else 0.0,
    )


def get_errors_by_provider(db: Session, filters: RangeFilters) -> list[ErrorBreakdownRow]:
    return _error_breakdown_by(apply_request_filters(select(LLMRequest), filters), "provider", db)


def get_errors_by_model(db: Session, filters: RangeFilters) -> list[ErrorBreakdownRow]:
    return _error_breakdown_by(apply_request_filters(select(LLMRequest), filters), "model", db)


def get_errors_by_code(db: Session, filters: RangeFilters) -> list[ErrorBreakdownRow]:
    stmt = apply_request_filters(select(LLMRequest), filters).where(LLMRequest.status == "error")
    return _error_breakdown_by(stmt, "error_type", db)


@dataclass(frozen=True)
class ModelSummaryRow:
    model: str
    provider: str
    request_count: int
    total_tokens: int
    total_cost: Decimal | None
    unknown_cost_count: int
    avg_cost_per_request: Decimal | None
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    error_rate: float


def _model_summary_query(filters: RangeFilters) -> Select[Any]:
    subq = apply_request_filters(select(LLMRequest), filters).subquery()
    p95 = func.percentile_cont(0.95).within_group(subq.c.latency_ms)
    return (
        select(
            subq.c.model,
            subq.c.provider,
            func.count(subq.c.id).label("request_count"),
            func.sum(subq.c.total_tokens).label("total_tokens"),
            func.sum(subq.c.total_cost).label("total_cost"),
            func.sum(case((subq.c.total_cost.is_(None), 1), else_=0)).label("unknown_cost_count"),
            func.avg(subq.c.latency_ms).label("avg_latency_ms"),
            p95.label("p95_latency_ms"),
            func.sum(case((subq.c.status == "error", 1), else_=0)).label("error_count"),
        )
        .group_by(subq.c.model, subq.c.provider)
        .order_by(subq.c.model)
    )


def _to_model_summary_row(row: Any) -> ModelSummaryRow:
    model: str = row[0]
    provider: str = row[1]
    request_count: int = row[2]
    total_tokens: int | None = row[3]
    total_cost: Decimal | None = row[4]
    unknown_cost_count: int | None = row[5]
    avg_latency_ms: float | None = row[6]
    p95_latency_ms: float | None = row[7]
    error_count: int = row[8] or 0
    avg_cost = (total_cost / request_count) if total_cost is not None and request_count else None
    return ModelSummaryRow(
        model=model,
        provider=provider,
        request_count=request_count,
        total_tokens=total_tokens or 0,
        total_cost=total_cost,
        unknown_cost_count=unknown_cost_count or 0,
        avg_cost_per_request=avg_cost,
        avg_latency_ms=float(avg_latency_ms) if avg_latency_ms is not None else None,
        p95_latency_ms=float(p95_latency_ms) if p95_latency_ms is not None else None,
        error_rate=(error_count / request_count) if request_count else 0.0,
    )


def get_model_summaries(db: Session, filters: RangeFilters) -> list[ModelSummaryRow]:
    rows = db.execute(_model_summary_query(filters)).all()
    return [_to_model_summary_row(row) for row in rows]


def get_model_summary(
    db: Session, filters: RangeFilters, model_name: str
) -> ModelSummaryRow | None:
    stmt = _model_summary_query(filters)
    row = db.execute(stmt.where(stmt.selected_columns.model == model_name)).first()
    return _to_model_summary_row(row) if row is not None else None

