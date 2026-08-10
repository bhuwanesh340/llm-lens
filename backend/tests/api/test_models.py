"""API tests for `/api/v1/models`, `/models/{model_id}` (T038, US2)."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_models_list_summary(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, model="gpt-4o-mini", total_cost=Decimal("0.00010000"), latency_ms=100)
    make_request(pg_session, model="gpt-4o-mini", total_cost=Decimal("0.00020000"), latency_ms=300)

    response = api_client.get("/api/v1/models")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["model"] == "gpt-4o-mini"
    assert rows[0]["request_count"] == 2
    assert Decimal(rows[0]["total_cost"]) == Decimal("0.00030000")


def test_model_detail_by_name(api_client: TestClient, pg_session: Session) -> None:
    make_request(
        pg_session,
        model="gpt-4o",
        status="error",
        error_type="TIMEOUT",
        total_cost=None,
        input_cost=None,
        output_cost=None,
    )
    make_request(pg_session, model="gpt-4o", status="success")

    response = api_client.get("/api/v1/models/gpt-4o")

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "gpt-4o"
    assert body["error_rate"] == 0.5


def test_model_detail_not_found(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/models/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"
