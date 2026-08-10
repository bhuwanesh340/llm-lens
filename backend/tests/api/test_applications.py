"""API tests for `/api/v1/applications` CRUD + "unassigned" grouping (T055, US4)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_application, make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_create_and_list_applications(api_client: TestClient) -> None:
    create_response = api_client.post(
        "/api/v1/applications", json={"name": "Support Bot", "slug": "support-bot"}
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["slug"] == "support-bot"

    list_response = api_client.get("/api/v1/applications")
    assert list_response.status_code == 200
    slugs = {app["slug"] for app in list_response.json()}
    assert "support-bot" in slugs


def test_duplicate_slug_returns_409(api_client: TestClient, pg_session: Session) -> None:
    make_application(pg_session, slug="duplicate-app")

    response = api_client.post(
        "/api/v1/applications", json={"name": "Another", "slug": "duplicate-app"}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_SLUG"


def test_get_update_delete_application(api_client: TestClient, pg_session: Session) -> None:
    application = make_application(pg_session, slug="crud-app")

    get_response = api_client.get(f"/api/v1/applications/{application.id}")
    assert get_response.status_code == 200

    patch_response = api_client.patch(
        f"/api/v1/applications/{application.id}", json={"name": "Renamed"}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Renamed"

    delete_response = api_client.delete(f"/api/v1/applications/{application.id}")
    assert delete_response.status_code == 204

    missing_response = api_client.get(f"/api/v1/applications/{application.id}")
    assert missing_response.status_code == 404


def test_unassigned_requests_form_distinct_bucket(
    api_client: TestClient, pg_session: Session
) -> None:
    application = make_application(pg_session, slug="tagged-app")
    make_request(pg_session, application_id=application.id)
    make_request(pg_session, application_id=None)

    response = api_client.get("/api/v1/costs/by-application")

    assert response.status_code == 200
    keys = {row["key"] for row in response.json()}
    assert "unassigned" in keys
    assert str(application.id) in keys
