"""Redaction module (T029).

Enforces constitution Principle II (Privacy-by-Default Telemetry): prompt
and response content is dropped unless the operator has explicitly opted
in via `STORE_PROMPTS`/`STORE_RESPONSES`. `error_message` is passed through
as-is but callers upstream (LiteLLM/normalizer) MUST NOT populate it with
prompt/response content (data-model.md validation rule).
"""

from __future__ import annotations

from app.core.config import Settings
from app.telemetry.events import NormalizedTelemetryEvent


def apply_redaction(
    event: NormalizedTelemetryEvent, settings: Settings
) -> NormalizedTelemetryEvent:
    """Return a copy of `event` with prompt/response redacted per settings."""

    return event.model_copy(
        update={
            "prompt": event.prompt if settings.store_prompts else None,
            "response": event.response if settings.store_responses else None,
        }
    )
