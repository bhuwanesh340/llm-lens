"""`Span` model (T205) — data-model.md `spans` table (feature 003).

One step within a `Trace`. Self-referencing `parent_span_id` forms the
nested call tree (FR-202). `parent_span_id` uses `ondelete=SET NULL`
rather than CASCADE so a missing/late parent never takes its children
down with it (FR-207 — orphans must render, not vanish).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base

SPAN_STATUSES = ("running", "success", "error")
SPAN_KINDS = ("llm", "tool", "retriever", "embedding", "chain", "agent", "custom")


class Span(Base):
    __tablename__ = "spans"
    __table_args__ = (
        CheckConstraint(f"status IN {SPAN_STATUSES}", name="ck_spans_status"),
        CheckConstraint(f"kind IN {SPAN_KINDS}", name="ck_spans_kind"),
        Index("ix_spans_trace_id", "trace_id"),
        Index("ix_spans_parent_span_id", "parent_span_id"),
        Index("ix_spans_started_at", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trace_id: Mapped[str] = mapped_column(
        ForeignKey("traces.id", ondelete="CASCADE"), nullable=False
    )
    parent_span_id: Mapped[str | None] = mapped_column(
        ForeignKey("spans.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="custom")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Populated only for kind == "llm" (FR-204).
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    output_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)

    # Redacted to NULL unless content logging is explicitly enabled (FR-206).
    input_: Mapped[dict[str, object] | None] = mapped_column("input", JSON, nullable=True)
    output_: Mapped[dict[str, object] | None] = mapped_column("output", JSON, nullable=True)

    error_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
