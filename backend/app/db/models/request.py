"""`LLMRequest` model (T014) — data-model.md `llm_requests` table.

The core observability unit: one row per attempted LLM call (FR-003, FR-004).
Depends on Provider/Model/Application/ApiKey (T010-T013).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base

# FR-003/FR-004: capture both success and error paths.
REQUEST_STATUSES = ("success", "error")

# spec §19 error categories.
ERROR_CATEGORIES = (
    "RATE_LIMIT",
    "AUTHENTICATION",
    "TIMEOUT",
    "BAD_REQUEST",
    "PROVIDER_ERROR",
    "UNKNOWN",
)


class LLMRequest(Base):
    __tablename__ = "llm_requests"
    __table_args__ = (
        CheckConstraint(f"status IN {REQUEST_STATUSES}", name="ck_llm_requests_status"),
        CheckConstraint("input_tokens >= 0", name="ck_llm_requests_input_tokens_nonneg"),
        CheckConstraint("output_tokens >= 0", name="ck_llm_requests_output_tokens_nonneg"),
        CheckConstraint("total_tokens >= 0", name="ck_llm_requests_total_tokens_nonneg"),
        CheckConstraint("latency_ms >= 0", name="ck_llm_requests_latency_ms_nonneg"),
        Index("ix_llm_requests_created_at", "created_at"),
        Index("ix_llm_requests_provider", "provider"),
        Index("ix_llm_requests_model", "model"),
        Index("ix_llm_requests_application_id", "application_id"),
        Index("ix_llm_requests_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    provider: Mapped[str] = mapped_column(
        ForeignKey("providers.name", ondelete="RESTRICT"), nullable=False
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False)

    status: Mapped[str] = mapped_column(String(16), nullable=False)

    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    input_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    output_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)

    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ttft_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), nullable=True
    )
    environment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True
    )

    error_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
