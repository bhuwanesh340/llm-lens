"""API tests for `/api/v1/costs*` endpoints (T037, US2)."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_project, make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_costs_by_model_known_and_unknown(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, model="gpt-4o-mini", total_cost=Decimal("0.00010000"))
    make_request(
        pg_session, model="gpt-4o-mini", total_cost=None, input_cost=None, output_cost=None
    )

    response = api_client.get("/api/v1/costs/by-model")

    assert response.status_code == 200
    rows = {row["key"]: row for row in response.json()}
    assert Decimal(rows["gpt-4o-mini"]["total_cost"]) == Decimal("0.00010000")
    assert rows["gpt-4o-mini"]["unknown_cost_count"] == 1
    assert rows["gpt-4o-mini"]["request_count"] == 2


def test_costs_by_provider(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, provider="openai", total_cost=Decimal("0.00010000"))
    make_request(pg_session, provider="anthropic", total_cost=Decimal("0.00020000"))

    response = api_client.get("/api/v1/costs/by-provider")

    assert response.status_code == 200
    keys = {row["key"] for row in response.json()}
    assert keys == {"openai", "anthropic"}


def test_costs_by_project_includes_unassigned_bucket(
    api_client: TestClient, pg_session: Session
) -> None:
    project = make_project(pg_session)
    make_request(pg_session, project_id=project.id, total_cost=Decimal("0.00010000"))
    make_request(pg_session, project_id=None, total_cost=Decimal("0.00020000"))

    response = api_client.get("/api/v1/costs/by-project")

    assert response.status_code == 200
    keys = {row["key"] for row in response.json()}
    assert "unassigned" in keys
    assert str(project.id) in keys


def test_costs_timeseries(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, total_cost=Decimal("0.00010000"))

    response = api_client.get("/api/v1/costs/timeseries")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_costs_invalid_date_range_returns_400(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/costs/by-model",
        params={"from": "2024-06-01T00:00:00Z", "to": "2024-01-01T00:00:00Z"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILTER"
