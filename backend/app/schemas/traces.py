"""Schemas for SDK trace/span ingestion (T207) — feature 003 Phase 1."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.span import SPAN_KINDS, SPAN_STATUSES
from app.db.models.trace import TRACE_STATUSES


class TraceIngestSpan(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    parent_span_id: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(default="custom")
    status: str = Field(default="success")

    started_at: datetime
    ended_at: datetime | None = None

    provider: str | None = None
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    # Redacted server-side unless content logging is enabled (FR-206) —
    # accepted here so the SDK never has to know the server's privacy config.
    input: dict[str, object] | None = None
    output: dict[str, object] | None = None

    error_type: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    metadata: dict[str, object] = Field(default_factory=dict)

    def validated_kind(self) -> str:
        return self.kind if self.kind in SPAN_KINDS else "custom"

    def validated_status(self) -> str:
        return self.status if self.status in SPAN_STATUSES else "success"


class TraceIngestPayload(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    status: str = Field(default="success")
    started_at: datetime
    ended_at: datetime | None = None
    environment: str | None = None
    # Name-only attribution path (FR-214/FR-217): used only when the caller
    # authenticated with the shared gateway token rather than a project API
    # key — resolved/auto-created exactly like feature 002 gateway traces.
    project: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    spans: list[TraceIngestSpan] = Field(default_factory=list)

    def validated_status(self) -> str:
        return self.status if self.status in TRACE_STATUSES else "success"
