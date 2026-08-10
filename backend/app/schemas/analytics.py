"""Response schemas for the analytics/usage/costs/errors/models endpoints
(Phase 4 US2, Phase 7 US5).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_requests: int
    total_cost: Decimal | None
    unknown_cost_count: int
    total_tokens: int
    avg_latency_ms: float | None
    error_rate: float
    active_models: int


class CostBreakdownItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    total_cost: Decimal | None
    unknown_cost_count: int
    request_count: int


class CostTimeseriesItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime
    total_cost: Decimal | None
    unknown_cost_count: int
    request_count: int


class UsageSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    avg_tokens_per_request: float


class UsageTimeseriesItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int


class UsageBreakdownItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int
    avg_tokens_per_request: float


class ErrorsSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_requests: int
    error_count: int
    error_rate: float


class ErrorBreakdownItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    error_count: int
    total_count: int
    error_rate: float


class ModelSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ModelDetailResponse(ModelSummaryItem):
    pass
