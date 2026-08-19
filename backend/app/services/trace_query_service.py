"""Trace list/detail queries for the Jinja+HTMX UI (T226, T228).

Kept separate from `trace_service.py` (ingestion) — this module is
read-only and shapes data specifically for rendering (pagination, span
counts, cost rollups, waterfall depth/offset/width), not persistence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.project import Project
from app.db.models.span import Span
from app.db.models.trace import Trace


@dataclass(frozen=True)
class TraceListItem:
    id: str
    name: str
    project_name: str | None
    status: str
    started_at: datetime
    duration_ms: int | None
    span_count: int
    total_cost: float | None


@dataclass(frozen=True)
class TraceListPage:
    items: list[TraceListItem]
    page: int
    page_size: int
    total: int

    @property
    def has_next(self) -> bool:
        return self.page * self.page_size < self.total

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // self.page_size))


def list_traces(
    db: Session,
    *,
    project_id: uuid.UUID | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> TraceListPage:
    """FR-219: paginated, filterable trace list with span_count/total_cost
    rollups (US3 acceptance scenario 1)."""

    query = select(Trace)
    if project_id is not None:
        query = query.where(Trace.project_id == project_id)
    if status is not None:
        query = query.where(Trace.status == status)
    if date_from is not None:
        query = query.where(Trace.started_at >= date_from)
    if date_to is not None:
        query = query.where(Trace.started_at <= date_to)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    rows = list(
        db.execute(
            query.order_by(Trace.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    trace_ids = [row.id for row in rows]
    span_counts: dict[str, int] = {}
    cost_totals: dict[str, float] = {}
    if trace_ids:
        rollup = db.execute(
            select(
                Span.trace_id,
                func.count(Span.id),
                func.coalesce(func.sum(Span.total_cost), 0),
            )
            .where(Span.trace_id.in_(trace_ids))
            .group_by(Span.trace_id)
        ).all()
        for trace_id, count, cost in rollup:
            span_counts[trace_id] = count
            cost_totals[trace_id] = float(cost or 0)

    project_ids = {row.project_id for row in rows if row.project_id is not None}
    project_names: dict[uuid.UUID, str] = {}
    if project_ids:
        for project in db.execute(select(Project).where(Project.id.in_(project_ids))).scalars():
            project_names[project.id] = project.name

    items = [
        TraceListItem(
            id=row.id,
            name=row.name,
            project_name=project_names.get(row.project_id) if row.project_id else None,
            status=row.status,
            started_at=row.started_at,
            duration_ms=row.duration_ms,
            span_count=span_counts.get(row.id, 0),
            total_cost=cost_totals.get(row.id),
        )
        for row in rows
    ]
    return TraceListPage(items=items, page=page, page_size=page_size, total=total)


@dataclass
class SpanNode:
    span: Span
    depth: int
    is_orphan: bool
    offset_ms: int
    width_pct: float
    children: list[SpanNode] = field(default_factory=list)


@dataclass(frozen=True)
class TraceDetail:
    trace: Trace
    project_name: str | None
    roots: list[SpanNode]
    flat_ordered: list[SpanNode]


def _duration_ms(started_at: datetime, ended_at: datetime | None) -> int:
    if ended_at is None:
        return 0
    return max(0, int((ended_at - started_at).total_seconds() * 1000))


def get_trace_detail(db: Session, trace_id: str) -> TraceDetail | None:
    """FR-207/FR-220: build the full span tree for the waterfall view.
    Spans whose `parent_span_id` doesn't resolve within this trace are
    rendered as top-level, flagged orphans — never dropped or errored."""

    trace = db.get(Trace, trace_id)
    if trace is None:
        return None

    spans = list(
        db.execute(select(Span).where(Span.trace_id == trace_id).order_by(Span.started_at))
        .scalars()
        .all()
    )
    by_id = {s.id: s for s in spans}

    children_map: dict[str | None, list[Span]] = {}
    for s in spans:
        key = s.parent_span_id if (s.parent_span_id is None or s.parent_span_id in by_id) else None
        children_map.setdefault(key, []).append(s)

    timeline_start = trace.started_at
    timeline_ms = trace.duration_ms
    if not timeline_ms:
        ends = [s.ended_at for s in spans if s.ended_at]
        timeline_ms = _duration_ms(timeline_start, max(ends)) if ends else 0
    timeline_ms = max(timeline_ms, 1)

    def build(span_list: list[Span], depth: int) -> list[SpanNode]:
        nodes = []
        for s in span_list:
            is_orphan = s.parent_span_id is not None and s.parent_span_id not in by_id
            offset_ms = _duration_ms(timeline_start, s.started_at)
            width_ms = s.duration_ms if s.duration_ms is not None else 0
            width_pct = max(1.0, min(100.0, (width_ms / timeline_ms) * 100)) if width_ms else 1.0
            node = SpanNode(
                span=s,
                depth=depth,
                is_orphan=is_orphan,
                offset_ms=offset_ms,
                width_pct=width_pct,
                children=build(children_map.get(s.id, []), depth + 1),
            )
            nodes.append(node)
        return nodes

    roots = build(children_map.get(None, []), 0)

    flat_ordered: list[SpanNode] = []

    def flatten(nodes: list[SpanNode]) -> None:
        for node in nodes:
            flat_ordered.append(node)
            flatten(node.children)

    flatten(roots)

    project_name = None
    if trace.project_id is not None:
        project = db.get(Project, trace.project_id)
        project_name = project.name if project else None

    return TraceDetail(
        trace=trace, project_name=project_name, roots=roots, flat_ordered=flat_ordered
    )
