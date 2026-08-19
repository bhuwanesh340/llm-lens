"""`Trace` model (T204) — data-model.md `traces` table (feature 003).

The root of a nested span tree. Client-generated `id` (ULID/UUID hex from
the SDK) so a trace can be referenced by its spans before the ingest
request even completes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.db.base import Base

TRACE_STATUSES = ("running", "success", "error")


class Trace(Base):
    __tablename__ = "traces"
    __table_args__ = (
        CheckConstraint(f"status IN {TRACE_STATUSES}", name="ck_traces_status"),
        Index("ix_traces_project_id", "project_id"),
        Index("ix_traces_started_at", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    environment: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Dialect-agnostic JSON (not JSONB) so this table is SQLite-portable from day one.
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
