"""API tests for `/api/v1/requests` list + detail (T050, US3)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_requests_list_paginated(api_client: TestClient, pg_session: Session) -> None:
    for _ in range(3):
        make_request(pg_session)

    response = api_client.get("/api/v1/requests", params={"page": 1, "page_size": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["meta"]["total_items"] == 3
    assert body["meta"]["total_pages"] == 2


def test_requests_list_filters_by_provider(api_client: TestClient, pg_session: Session) -> None:
    make_request(pg_session, provider="openai")
    make_request(pg_session, provider="anthropic")

    response = api_client.get("/api/v1/requests", params={"provider": "openai"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["provider"] == "openai"


def test_requests_list_invalid_sort_returns_400(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/requests", params={"sort": "not_a_column"})

    assert response.status_code == 400


def test_request_detail_includes_error_info(api_client: TestClient, pg_session: Session) -> None:
    record = make_request(
        pg_session,
        status="error",
        error_type="TIMEOUT",
        error_code="ETIMEDOUT",
        error_message="Upstream provider timed out",
        total_cost=None,
        input_cost=None,
        output_cost=None,
    )

    response = api_client.get(f"/api/v1/requests/{record.request_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["error_type"] == "TIMEOUT"
    assert body["error_message"] == "Upstream provider timed out"
    assert "prompt" not in body
    assert "response" not in body


def test_request_detail_not_found(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/requests/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "REQUEST_NOT_FOUND"
