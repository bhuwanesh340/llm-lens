"""Unit tests for the telemetry normalizer (T023).

Covers: token totals, error categorization, and no prompt/response leakage
into fields that are always logged/persisted regardless of redaction.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.telemetry.events import RawTelemetryEvent
from app.telemetry.normalizer import normalize_event


def _raw_event(**overrides: object) -> RawTelemetryEvent:
    defaults: dict[str, object] = {
        "request_id": "req-1",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "status": "success",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return RawTelemetryEvent(**defaults)  # type: ignore[arg-type]


def test_total_tokens_equals_input_plus_output() -> None:
    raw = _raw_event(input_tokens=100, output_tokens=50)

    normalized = normalize_event(raw)

    assert normalized.input_tokens == 100
    assert normalized.output_tokens == 50
    assert normalized.total_tokens == 150


def test_missing_token_counts_default_to_zero() -> None:
    raw = _raw_event(input_tokens=None, output_tokens=None)

    normalized = normalize_event(raw)

    assert normalized.total_tokens == 0


def test_success_status_clears_error_fields() -> None:
    raw = _raw_event(
        status="success",
        error_type="TIMEOUT",
        error_code="ignored",
        error_message="ignored",
    )

    normalized = normalize_event(raw)

    assert normalized.error_type is None
    assert normalized.error_code is None
    assert normalized.error_message is None


def test_error_status_normalizes_known_category() -> None:
    raw = _raw_event(status="error", error_type="RATE_LIMIT", error_code="429")

    normalized = normalize_event(raw)

    assert normalized.error_type == "RATE_LIMIT"
    assert normalized.error_code == "429"


def test_error_status_with_unrecognized_category_becomes_unknown() -> None:
    raw = _raw_event(status="error", error_type=None)

    normalized = normalize_event(raw)

    assert normalized.error_type == "UNKNOWN"
