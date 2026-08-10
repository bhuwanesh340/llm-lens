"""Integration test (T024): telemetry event -> collector -> PostgreSQL row,
for both success and failure paths, plus duplicate/unconfigured-model
rejection.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models.model import Model
from app.db.models.provider import Provider
from app.db.models.request import LLMRequest
from app.telemetry.collector import (
    DuplicateRequestIdError,
    UnconfiguredModelError,
    collect_telemetry_event,
)
from app.telemetry.events import RawTelemetryEvent
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


@pytest.fixture()
def settings() -> Settings:
    return Settings(STORE_PROMPTS=False, STORE_RESPONSES=False)


def _register_openai_gpt4o_mini(db: Session) -> None:
    provider = Provider(name="openai", display_name="OpenAI", enabled=True)
    db.add(provider)
    db.flush()
    db.add(
        Model(
            provider_id=provider.id,
            model_name="gpt-4o-mini",
            display_name="GPT-4o mini",
            input_price_per_1m=None,
            output_price_per_1m=None,
            currency="USD",
            is_active=True,
        )
    )
    db.commit()


def test_success_event_is_persisted(pg_session: Session, settings: Settings) -> None:
    _register_openai_gpt4o_mini(pg_session)
    raw = RawTelemetryEvent(
        request_id="req-success-1",
        provider="openai",
        model="gpt-4o-mini",
        status="success",
        created_at=datetime.now(UTC),
        input_tokens=100,
        output_tokens=50,
        latency_ms=250,
    )

    record = collect_telemetry_event(pg_session, raw, settings)

    assert record.request_id == "req-success-1"
    assert record.status == "success"
    assert record.total_tokens == 150

    stored = pg_session.execute(
        select(LLMRequest).where(LLMRequest.request_id == "req-success-1")
    ).scalar_one()
    assert stored.status == "success"


def test_failure_event_is_persisted_with_error_info(
    pg_session: Session, settings: Settings
) -> None:
    _register_openai_gpt4o_mini(pg_session)
    raw = RawTelemetryEvent(
        request_id="req-failure-1",
        provider="openai",
        model="gpt-4o-mini",
        status="error",
        created_at=datetime.now(UTC),
        latency_ms=5000,
        error_type="TIMEOUT",
        error_code="504",
        error_message="Upstream provider timed out",
    )

    record = collect_telemetry_event(pg_session, raw, settings)

    assert record.status == "error"
    assert record.error_type == "TIMEOUT"
    assert record.error_code == "504"


def test_duplicate_request_id_is_rejected(pg_session: Session, settings: Settings) -> None:
    _register_openai_gpt4o_mini(pg_session)
    raw = RawTelemetryEvent(
        request_id="req-dup-1",
        provider="openai",
        model="gpt-4o-mini",
        status="success",
        created_at=datetime.now(UTC),
        input_tokens=10,
        output_tokens=5,
        latency_ms=100,
    )
    collect_telemetry_event(pg_session, raw, settings)

    with pytest.raises(DuplicateRequestIdError):
        collect_telemetry_event(pg_session, raw, settings)


def test_unconfigured_model_is_rejected(pg_session: Session, settings: Settings) -> None:
    raw = RawTelemetryEvent(
        request_id="req-unconfigured-1",
        provider="openai",
        model="not-a-real-model",
        status="success",
        created_at=datetime.now(UTC),
        input_tokens=10,
        output_tokens=5,
        latency_ms=100,
    )

    with pytest.raises(UnconfiguredModelError):
        collect_telemetry_event(pg_session, raw, settings)
