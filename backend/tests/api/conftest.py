"""Shared fixtures for API tests (T035-T038, T050, T055, T060).

Require a real PostgreSQL instance (same constraint as
`tests/integration/conftest.py` — JSONB support for `LLMRequest.metadata_`).
Uses `dependency_overrides` to inject the Postgres-backed session and to
bypass the real admin-session cookie flow for tests that aren't specifically
exercising authentication.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import require_admin_session
from app.db.models.project import Project
from app.db.models.provider import Provider
from app.db.models.request import LLMRequest
from app.db.session import get_db
from app.main import app
from tests.integration.conftest import pg_session, requires_postgres  # noqa: F401

__all__ = ["requires_postgres", "pg_session", "api_client", "make_request", "make_project"]


@pytest.fixture()
def api_client(pg_session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: pg_session
    app.dependency_overrides[require_admin_session] = lambda: "admin@example.com"
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def make_project(db: Session, *, name: str = "Test App", slug: str = "test-app") -> Project:
    project = Project(name=name, slug=slug)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def make_request(
    db: Session,
    *,
    request_id: str | None = None,
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    status: str = "success",
    input_tokens: int = 100,
    output_tokens: int = 50,
    total_cost: Decimal | None = Decimal("0.00010000"),
    input_cost: Decimal | None = Decimal("0.00005000"),
    output_cost: Decimal | None = Decimal("0.00005000"),
    latency_ms: int = 250,
    project_id: uuid.UUID | None = None,
    environment: str | None = None,
    error_type: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    created_at: datetime | None = None,
) -> LLMRequest:
    provider_row = db.query(Provider).filter(Provider.name == provider).one_or_none()
    if provider_row is None:
        db.add(Provider(name=provider, display_name=provider.title(), enabled=True))
        db.commit()

    record = LLMRequest(
        request_id=request_id or f"req_{uuid.uuid4().hex}",
        created_at=created_at or datetime.now(UTC),
        provider=provider,
        model=model,
        status=status,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
        latency_ms=latency_ms,
        project_id=project_id,
        environment=environment,
        error_type=error_type,
        error_code=error_code,
        error_message=error_message,
        metadata_={},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

