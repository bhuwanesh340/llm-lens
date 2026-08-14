"""Unit tests for redaction (T023) — constitution Principle II:
Privacy-by-Default Telemetry.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import Settings
from app.telemetry.events import NormalizedTelemetryEvent
from app.telemetry.redaction import apply_redaction


def _event(
    prompt: object = "secret prompt", response: object = "secret response"
) -> NormalizedTelemetryEvent:
    return NormalizedTelemetryEvent(
        request_id="req-1",
        provider="openai",
        model="gpt-4o-mini",
        status="success",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        completed_at=None,
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        latency_ms=100,
        ttft_ms=None,
        project=None,
        project_id=None,
        environment=None,
        api_key_id=None,
        error_type=None,
        error_code=None,
        error_message=None,
        prompt=prompt,
        response=response,
        metadata={},
    )


def test_default_settings_redact_both_prompt_and_response() -> None:
    settings = Settings(STORE_PROMPTS=False, STORE_RESPONSES=False)

    redacted = apply_redaction(_event(), settings)

    assert redacted.prompt is None
    assert redacted.response is None


def test_store_prompts_true_keeps_prompt_only() -> None:
    settings = Settings(STORE_PROMPTS=True, STORE_RESPONSES=False)

    redacted = apply_redaction(_event(), settings)

    assert redacted.prompt == "secret prompt"
    assert redacted.response is None


def test_store_responses_true_keeps_response_only() -> None:
    settings = Settings(STORE_PROMPTS=False, STORE_RESPONSES=True)

    redacted = apply_redaction(_event(), settings)

    assert redacted.prompt is None
    assert redacted.response == "secret response"
