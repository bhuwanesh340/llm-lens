"""Response schemas for the Request Explorer (T050-T052, US3)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RequestListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: str
    created_at: datetime
    provider: str
    model: str
    application_id: UUID | None
    environment: str | None
    status: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost: Decimal | None
    latency_ms: int


class RequestDetail(RequestListItem):
    completed_at: datetime | None
    input_cost: Decimal | None
    output_cost: Decimal | None
    ttft_ms: int | None
    api_key_id: UUID | None
    error_type: str | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, object]
