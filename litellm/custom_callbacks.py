"""LiteLLM custom callback (T032): forwards each completed request (success
or failure) to the backend's telemetry ingestion webhook
(`POST /api/v1/telemetry/events`).

Constitution Principle I: this file lives in `litellm/` (gateway
configuration), not in the backend application code — it only shapes and
forwards LiteLLM's own event data, it never re-implements provider calls.

Loaded via `litellm_settings.callbacks: custom_callbacks.proxy_handler_instance`
in `config.yaml`.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from json import dumps
from typing import Any

import httpx
from litellm.integrations.custom_logger import CustomLogger

BACKEND_TELEMETRY_URL = os.environ.get(
    "BACKEND_TELEMETRY_URL", "http://backend:8000/api/v1/telemetry/events"
)
LITELLM_CALLBACK_TOKEN = os.environ.get("LITELLM_CALLBACK_TOKEN", "")

_ERROR_TYPE_MAP: dict[str, str] = {
    "RateLimitError": "RATE_LIMIT",
    "AuthenticationError": "AUTHENTICATION",
    "Timeout": "TIMEOUT",
    "APITimeoutError": "TIMEOUT",
    "BadRequestError": "BAD_REQUEST",
    "InvalidRequestError": "BAD_REQUEST",
    "APIError": "PROVIDER_ERROR",
    "ServiceUnavailableError": "PROVIDER_ERROR",
}


def _extract_usage(response_obj: Any) -> tuple[int, int]:
    usage = getattr(response_obj, "usage", None)
    if usage is None and isinstance(response_obj, dict):
        usage = response_obj.get("usage")
    if usage is None:
        return 0, 0
    input_tokens = getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "completion_tokens", None)
    if isinstance(usage, dict):
        input_tokens = usage.get("prompt_tokens", input_tokens)
        output_tokens = usage.get("completion_tokens", output_tokens)
    return int(input_tokens or 0), int(output_tokens or 0)


def _extract_metadata(kwargs: dict[str, Any]) -> dict[str, Any]:
    litellm_params = kwargs.get("litellm_params") or {}
    return litellm_params.get("metadata") or {}


# Promoted to top-level telemetry fields rather than free-form metadata.
_RESERVED_METADATA_KEYS = {"project", "project_id", "environment", "api_key_id"}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _build_base_payload(
    kwargs: dict[str, Any], start_time: datetime, end_time: datetime
) -> dict[str, Any]:
    metadata = _extract_metadata(kwargs)
    request_id = kwargs.get("litellm_call_id") or str(uuid.uuid4())
    latency_ms = max(int((end_time - start_time).total_seconds() * 1000), 0)

    return {
        "request_id": request_id,
        "provider": kwargs.get("custom_llm_provider") or "unknown",
        "model": kwargs.get("model") or "unknown",
        "created_at": start_time.astimezone(timezone.utc).isoformat(),
        "completed_at": end_time.astimezone(timezone.utc).isoformat(),
        "latency_ms": latency_ms,
        "project": _json_safe(metadata.get("project")),
        "project_id": _json_safe(metadata.get("project_id")),
        "environment": _json_safe(metadata.get("environment")),
        "api_key_id": _json_safe(metadata.get("api_key_id")),
        "metadata": _json_safe(
            {k: v for k, v in metadata.items() if k not in _RESERVED_METADATA_KEYS}
        ),
    }


async def _post_event(payload: dict[str, Any]) -> None:
    headers = {"X-Internal-Token": LITELLM_CALLBACK_TOKEN, "Content-Type": "application/json"}
    body = dumps(payload, ensure_ascii=False, allow_nan=False, default=str)
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(BACKEND_TELEMETRY_URL, content=body, headers=headers)
        except httpx.HTTPError:
            # Telemetry must never break the LLM response path (plan.md
            # Performance Goals). Failures here are swallowed; operators can
            # observe gaps via backend Prometheus metrics/logs.
            pass


class TelemetryCallbackHandler(CustomLogger):
    """Forwards success/failure events to the backend telemetry webhook."""

    async def async_log_success_event(
        self, kwargs: dict[str, Any], response_obj: Any, start_time: datetime, end_time: datetime
    ) -> None:
        input_tokens, output_tokens = _extract_usage(response_obj)
        payload = _build_base_payload(kwargs, start_time, end_time)
        payload.update(
            {
                "status": "success",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
        )
        await _post_event(payload)

    async def async_log_failure_event(
        self, kwargs: dict[str, Any], response_obj: Any, start_time: datetime, end_time: datetime
    ) -> None:
        exception = kwargs.get("exception")
        exception_type = type(exception).__name__ if exception is not None else "UNKNOWN"
        payload = _build_base_payload(kwargs, start_time, end_time)
        payload.update(
            {
                "status": "error",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "error_type": _ERROR_TYPE_MAP.get(exception_type, "UNKNOWN"),
                "error_code": exception_type,
                "error_message": str(exception) if exception is not None else None,
            }
        )
        await _post_event(payload)


proxy_handler_instance = TelemetryCallbackHandler()
