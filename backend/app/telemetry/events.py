"""Normalized telemetry event schema (T027).

This is the internal representation produced by the LiteLLM callback
integration (T032) before normalization (T028), redaction (T029), and cost
calculation (T030) are applied and the result persisted as an `LLMRequest`
row (T031).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ErrorCategory = Literal[
    "RATE_LIMIT",
    "AUTHENTICATION",
    "TIMEOUT",
    "BAD_REQUEST",
    "PROVIDER_ERROR",
    "UNKNOWN",
]


class RawTelemetryEvent(BaseModel):
    """Raw shape as received from the LiteLLM callback, prior to normalization.

    Deliberately permissive (optional fields) because provider responses
    are not uniformly complete — the normalizer is responsible for filling
    gaps and enforcing invariants.
    """

    request_id: str
    provider: str
    model: str
    status: Literal["success", "error"]
    created_at: datetime
    completed_at: datetime | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    latency_ms: int | None = None
    ttft_ms: int | None = None

    application_id: str | None = None
    environment: str | None = None
    api_key_id: str | None = None

    error_type: ErrorCategory | None = None
    error_code: str | None = None
    error_message: str | None = None

    # Raw prompt/response content — only ever persisted if content logging
    # is explicitly enabled (redaction.py); never logged (logging.py redacts
    # any field literally named "prompt"/"response" as defense in depth).
    prompt: object | None = Field(default=None, repr=False)
    response: object | None = Field(default=None, repr=False)

    metadata: dict[str, object] = Field(default_factory=dict)


class NormalizedTelemetryEvent(BaseModel):
    """Post-normalization event, ready for redaction + cost calculation."""

    request_id: str
    provider: str
    model: str
    status: Literal["success", "error"]
    created_at: datetime
    completed_at: datetime | None

    input_tokens: int
    output_tokens: int
    total_tokens: int

    latency_ms: int
    ttft_ms: int | None

    application_id: str | None
    environment: str | None
    api_key_id: str | None

    error_type: ErrorCategory | None
    error_code: str | None
    error_message: str | None

    prompt: object | None = Field(default=None, repr=False)
    response: object | None = Field(default=None, repr=False)

    metadata: dict[str, object]
