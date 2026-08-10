"""API tests for `/api/v1/usage*` endpoints (T036, US2)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_usage_summary(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, input_tokens=100, output_tokens=50)
    make_request(pg_session, input_tokens=200, output_tokens=100)

    response = api_client.get("/api/v1/usage")

    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 2
    assert body["input_tokens"] == 300
    assert body["output_tokens"] == 150
    assert body["total_tokens"] == 450


def test_usage_by_model(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, model="gpt-4o-mini", input_tokens=100, output_tokens=50)
    make_request(pg_session, model="gpt-4o", input_tokens=200, output_tokens=100)

    response = api_client.get("/api/v1/usage/by-model")

    assert response.status_code == 200
    keys = {row["key"] for row in response.json()}
    assert keys == {"gpt-4o-mini", "gpt-4o"}


def test_usage_by_provider(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, provider="openai")
    make_request(pg_session, provider="anthropic")

    response = api_client.get("/api/v1/usage/by-provider")

    assert response.status_code == 200
    keys = {row["key"] for row in response.json()}
    assert keys == {"openai", "anthropic"}


def test_usage_timeseries(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session)

    response = api_client.get("/api/v1/usage/timeseries")

    assert response.status_code == 200
    assert len(response.json()) >= 1
