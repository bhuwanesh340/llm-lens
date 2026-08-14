"""Telemetry collector (T031, T033, T034).

Consumes a normalized+redacted telemetry event and persists it as an
`LLMRequest` row, applying:

- duplicate `request_id` rejection (data-model.md unique constraint,
  research.md §6 edge case),
- unconfigured provider/model rejection (T033, FR-025),
- centralized cost calculation (T030),
- structured, secret/prompt/response-free logging (T034).
"""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.metrics import telemetry_events_failed_total, telemetry_events_total
from app.db.models.request import LLMRequest
from app.providers.registry import is_model_configured
from app.services.cost_service import calculate_cost
from app.services.project_service import (
    InvalidProjectNameError,
    resolve_or_create_project,
)
from app.telemetry.events import NormalizedTelemetryEvent, RawTelemetryEvent
from app.telemetry.normalizer import normalize_event
from app.telemetry.redaction import apply_redaction

logger = get_logger(__name__)


class DuplicateRequestIdError(Exception):
    """Raised when a telemetry event's `request_id` already exists."""

    def __init__(self, request_id: str) -> None:
        super().__init__(f"Duplicate request_id: {request_id}")
        self.request_id = request_id


class UnconfiguredModelError(Exception):
    """Raised when a telemetry event references an unknown/disabled
    provider/model pair (FR-025 — clear, actionable error)."""

    def __init__(self, provider: str, model: str) -> None:
        super().__init__(
            f"Provider '{provider}' / model '{model}' is not configured or is disabled. "
            "Add it to litellm/config.yaml and the `models` table before use."
        )
        self.provider = provider
        self.model = model


def _resolve_project_id(db: Session, event: NormalizedTelemetryEvent) -> uuid.UUID | None:
    """Resolve the owning project, auto-creating it for unseen names (FR-102).

    An explicit `project_id` (set by an authenticated project API key) wins
    over a `project` name supplied in request metadata (FR-119). An invalid
    name is recorded as unassigned rather than dropping the trace (FR-104).
    """

    if event.project_id:
        try:
            return uuid.UUID(event.project_id)
        except ValueError:
            logger.warning("telemetry_invalid_project_id", request_id=event.request_id)

    if event.project:
        try:
            return resolve_or_create_project(db, event.project).id
        except InvalidProjectNameError:
            logger.warning("telemetry_invalid_project_name", request_id=event.request_id)

    return None


def _to_orm(
    event: NormalizedTelemetryEvent, db: Session, project_id: uuid.UUID | None
) -> LLMRequest:
    cost = calculate_cost(
        db,
        provider=event.provider,
        model=event.model,
        input_tokens=event.input_tokens,
        output_tokens=event.output_tokens,
    )
    return LLMRequest(
        request_id=event.request_id,
        created_at=event.created_at,
        completed_at=event.completed_at,
        provider=event.provider,
        model=event.model,
        status=event.status,
        input_tokens=event.input_tokens,
        output_tokens=event.output_tokens,
        total_tokens=event.total_tokens,
        input_cost=cost.input_cost,
        output_cost=cost.output_cost,
        total_cost=cost.total_cost,
        latency_ms=event.latency_ms,
        ttft_ms=event.ttft_ms,
        project_id=project_id,
        environment=event.environment,
        api_key_id=event.api_key_id,
        error_type=event.error_type,
        error_code=event.error_code,
        error_message=event.error_message,
        metadata_=event.metadata,
    )


def collect_telemetry_event(
    db: Session, raw: RawTelemetryEvent, settings: Settings | None = None
) -> LLMRequest:
    """Normalize, redact, price, validate, and persist one telemetry event.

    Raises `UnconfiguredModelError` if the provider/model pair is not
    registered/enabled, and `DuplicateRequestIdError` if `request_id` has
    already been recorded. Both are caught by callers (e.g. the LiteLLM
    callback endpoint) and translated into actionable HTTP errors.
    """

    settings = settings or get_settings()

    if not is_model_configured(db, raw.provider, raw.model):
        telemetry_events_failed_total.labels(reason="unconfigured_model").inc()
        logger.warning(
            "telemetry_rejected_unconfigured_model",
            provider=raw.provider,
            model=raw.model,
            request_id=raw.request_id,
        )
        raise UnconfiguredModelError(raw.provider, raw.model)

    normalized = normalize_event(raw)
    redacted = apply_redaction(normalized, settings)

    orm_request = _to_orm(redacted, db, _resolve_project_id(db, redacted))
    db.add(orm_request)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        telemetry_events_failed_total.labels(reason="duplicate_request_id").inc()
        logger.warning(
            "telemetry_rejected_duplicate_request_id",
            provider=raw.provider,
            model=raw.model,
            request_id=raw.request_id,
        )
        raise DuplicateRequestIdError(raw.request_id) from exc

    db.refresh(orm_request)
    telemetry_events_total.labels(provider=raw.provider, status=raw.status).inc()
    logger.info(
        "telemetry_recorded",
        provider=raw.provider,
        model=raw.model,
        status=raw.status,
        request_id=raw.request_id,
        latency_ms=redacted.latency_ms,
    )
    return orm_request
