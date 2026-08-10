"""API tests for `/api/v1/overview` (T035, US2)."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_overview_unauthenticated_returns_401() -> None:
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/api/v1/overview")
    assert response.status_code == 401


def test_overview_aggregates_known_costs(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, total_cost=Decimal("0.00010000"), latency_ms=100)
    make_request(pg_session, total_cost=Decimal("0.00020000"), latency_ms=200)

    response = api_client.get("/api/v1/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 2
    assert Decimal(body["total_cost"]) == Decimal("0.00030000")
    assert body["unknown_cost_count"] == 0
    assert body["error_rate"] == 0.0


def test_overview_reports_unknown_cost_count(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, total_cost=Decimal("0.00010000"))
    make_request(pg_session, total_cost=None, input_cost=None, output_cost=None)

    response = api_client.get("/api/v1/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 2
    assert Decimal(body["total_cost"]) == Decimal("0.00010000")
    assert body["unknown_cost_count"] == 1


def test_overview_computes_error_rate(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, status="success")
    make_request(
        pg_session,
        status="error",
        error_type="TIMEOUT",
        total_cost=None,
        input_cost=None,
        output_cost=None,
    )

    response = api_client.get("/api/v1/overview")

    assert response.status_code == 200
    assert response.json()["error_rate"] == 0.5
