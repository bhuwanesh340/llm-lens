"""Trace/span ingestion (T209) — feature 003 Phase 1.

Persists the nested run tree reported by the SDK. Idempotent by design
(FR-208): re-posting the same trace/span id is a no-op, so the SDK's
at-least-once batching sender can retry freely without duplicating data.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models.span import Span
from app.db.models.trace import Trace
from app.schemas.traces import TraceIngestPayload, TraceIngestSpan
from app.services.cost_service import calculate_cost


def _duration_ms(started_at: datetime, ended_at: datetime | None) -> int | None:
    if ended_at is None:
        return None
    return max(0, int((ended_at - started_at).total_seconds() * 1000))


def _redact(value: dict[str, object] | None, *, keep: bool) -> dict[str, object] | None:
    return value if keep and value is not None else None


def _upsert_trace(db: Session, project_id: uuid.UUID | None, payload: TraceIngestPayload) -> Trace:
    trace = db.get(Trace, payload.id)
    if trace is None:
        trace = Trace(
            id=payload.id,
            project_id=project_id,
            name=payload.name,
            status=payload.validated_status(),
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            duration_ms=_duration_ms(payload.started_at, payload.ended_at),
            environment=payload.environment,
            metadata_=payload.metadata,
        )
        db.add(trace)
    else:
        # Later ingestion of the same trace (e.g. the run completed) updates
        # terminal fields only — never re-attributes an existing trace.
        trace.status = payload.validated_status()
        trace.ended_at = payload.ended_at or trace.ended_at
        trace.duration_ms = _duration_ms(trace.started_at, trace.ended_at)
    return trace


def _insert_span_if_absent(
    db: Session,
    trace_id: str,
    span_payload: TraceIngestSpan,
    settings: Settings,
) -> None:
    if db.get(Span, span_payload.id) is not None:
        return  # FR-208: duplicate delivery is a no-op.

    input_cost = output_cost = total_cost = None
    input_tokens = span_payload.input_tokens
    output_tokens = span_payload.output_tokens
    if (
        span_payload.validated_kind() == "llm"
        and span_payload.provider
        and span_payload.model
        and input_tokens is not None
        and output_tokens is not None
    ):
        cost = calculate_cost(
            db, span_payload.provider, span_payload.model, input_tokens, output_tokens
        )
        input_cost, output_cost, total_cost = cost.input_cost, cost.output_cost, cost.total_cost

    total_tokens = (
        input_tokens + output_tokens
        if input_tokens is not None and output_tokens is not None
        else None
    )

    db.add(
        Span(
            id=span_payload.id,
            trace_id=trace_id,
            parent_span_id=span_payload.parent_span_id,
            name=span_payload.name,
            kind=span_payload.validated_kind(),
            status=span_payload.validated_status(),
            started_at=span_payload.started_at,
            ended_at=span_payload.ended_at,
            duration_ms=_duration_ms(span_payload.started_at, span_payload.ended_at),
            provider=span_payload.provider,
            model=span_payload.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            input_=_redact(span_payload.input, keep=settings.store_prompts),
            output_=_redact(span_payload.output, keep=settings.store_responses),
            error_type=span_payload.error_type,
            error_code=span_payload.error_code,
            error_message=span_payload.error_message,
            metadata_=span_payload.metadata,
        )
    )


def ingest_trace(db: Session, project_id: uuid.UUID | None, payload: TraceIngestPayload) -> Trace:
    """Persist a trace and its spans. Parent spans need not precede children
    (FR-207) — the FK is nullable and unresolved parents simply render as
    orphans in the UI rather than blocking ingestion."""

    settings = get_settings()
    trace = _upsert_trace(db, project_id, payload)
    for span_payload in payload.spans:
        _insert_span_if_absent(db, payload.id, span_payload, settings)
    db.commit()
    db.refresh(trace)
    return trace
