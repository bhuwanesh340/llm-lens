"""API tests for `/api/v1/errors*` endpoints (T060, US5)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_errors_summary(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, status="success")
    make_request(
        pg_session,
        status="error",
        error_type="RATE_LIMIT",
        total_cost=None,
        input_cost=None,
        output_cost=None,
    )

    response = api_client.get("/api/v1/errors")

    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 2
    assert body["error_count"] == 1
    assert body["error_rate"] == 0.5


def test_errors_by_provider(api_client: TestClient, pg_session: Session) -> None:
    make_request(
        pg_session,
        provider="openai",
        status="error",
        error_type="TIMEOUT",
        total_cost=None,
        input_cost=None,
        output_cost=None,
    )
    make_request(pg_session, provider="anthropic", status="success")

    response = api_client.get("/api/v1/errors/by-provider")

    assert response.status_code == 200
    rows = {row["key"]: row for row in response.json()}
    assert rows["openai"]["error_count"] == 1
    assert rows["anthropic"]["error_count"] == 0


def test_errors_by_code_only_covers_errors(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, status="success")
    make_request(
        pg_session,
        status="error",
        error_type="BAD_REQUEST",
        total_cost=None,
        input_cost=None,
        output_cost=None,
    )

    response = api_client.get("/api/v1/errors/by-code")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["key"] == "BAD_REQUEST"
    assert rows[0]["total_count"] == 1
