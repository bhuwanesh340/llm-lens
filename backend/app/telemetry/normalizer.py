"""Telemetry normalizer (T028).

Normalizes raw LiteLLM callback data into a `NormalizedTelemetryEvent`:
fills token totals, defaults missing numeric fields to 0, and enforces
`total_tokens = input_tokens + output_tokens` (data-model.md validation
rule — enforced here rather than as a DB constraint, to tolerate partial
provider data gracefully).
"""

from __future__ import annotations

from app.telemetry.events import NormalizedTelemetryEvent, RawTelemetryEvent

_VALID_ERROR_CATEGORIES = {
    "RATE_LIMIT",
    "AUTHENTICATION",
    "TIMEOUT",
    "BAD_REQUEST",
    "PROVIDER_ERROR",
    "UNKNOWN",
}


def _normalize_error_type(status: str, error_type: str | None) -> str | None:
    if status == "success":
        return None
    if error_type in _VALID_ERROR_CATEGORIES:
        return error_type
    return "UNKNOWN"


def normalize_event(raw: RawTelemetryEvent) -> NormalizedTelemetryEvent:
    """Convert a raw callback event into a normalized telemetry event."""

    input_tokens = raw.input_tokens or 0
    output_tokens = raw.output_tokens or 0
    total_tokens = input_tokens + output_tokens

    is_error = raw.status == "error"

    return NormalizedTelemetryEvent(
        request_id=raw.request_id,
        provider=raw.provider,
        model=raw.model,
        status=raw.status,
        created_at=raw.created_at,
        completed_at=raw.completed_at,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=raw.latency_ms or 0,
        ttft_ms=raw.ttft_ms,
        application_id=raw.application_id,
        environment=raw.environment,
        api_key_id=raw.api_key_id,
        error_type=_normalize_error_type(raw.status, raw.error_type) if is_error else None,
        error_code=raw.error_code if is_error else None,
        error_message=raw.error_message if is_error else None,
        prompt=raw.prompt,
        response=raw.response,
        metadata=raw.metadata,
    )
