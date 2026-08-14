"""API tests for `/api/v1/projects` CRUD + "unassigned" grouping (T113)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.conftest import make_project, make_request
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def test_create_and_list_projects(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/projects", json={"name": "Support Bot", "slug": "support-bot"}
    )

    assert response.status_code == 201
    assert response.json()["slug"] == "support-bot"
    # Explicitly created projects are distinguishable from auto-created ones (FR-106).
    assert response.json()["auto_created"] is False

    list_response = api_client.get("/api/v1/projects")

    assert list_response.status_code == 200
    assert any(project["slug"] == "support-bot" for project in list_response.json())


def test_create_project_derives_slug_from_name(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/projects", json={"name": "My Cool App"})

    assert response.status_code == 201
    assert response.json()["slug"] == "my-cool-app"


def test_create_project_rejects_blank_name(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/projects", json={"name": "   "})

    assert response.status_code == 422


def test_duplicate_slug_returns_409(api_client: TestClient, pg_session: Session) -> None:
    make_project(pg_session, slug="duplicate-app")

    response = api_client.post(
        "/api/v1/projects", json={"name": "Another", "slug": "duplicate-app"}
    )

    assert response.status_code == 409


def test_get_update_delete_project(api_client: TestClient, pg_session: Session) -> None:
    project = make_project(pg_session, slug="crud-app")

    get_response = api_client.get(f"/api/v1/projects/{project.id}")
    assert get_response.status_code == 200

    patch_response = api_client.patch(
        f"/api/v1/projects/{project.id}", json={"name": "Renamed"}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Renamed"

    delete_response = api_client.delete(f"/api/v1/projects/{project.id}")
    assert delete_response.status_code == 204

    missing_response = api_client.get(f"/api/v1/projects/{project.id}")
    assert missing_response.status_code == 404


def test_costs_group_by_project_and_unassigned(
    api_client: TestClient, pg_session: Session
) -> None:
    project = make_project(pg_session, slug="tagged-app")
    make_request(pg_session, project_id=project.id)
    make_request(pg_session, project_id=None)

    response = api_client.get("/api/v1/costs/by-project")

    assert response.status_code == 200
    keys = {row["key"] for row in response.json()}
    assert "unassigned" in keys
    assert str(project.id) in keys


def test_deleting_project_preserves_its_requests(
    api_client: TestClient, pg_session: Session
) -> None:
    """FR-111: history survives project deletion (FK is SET NULL)."""

    project = make_project(pg_session, slug="doomed-app")
    make_request(pg_session, project_id=project.id)

    assert api_client.delete(f"/api/v1/projects/{project.id}").status_code == 204

    requests_response = api_client.get("/api/v1/requests")
    assert requests_response.status_code == 200
    assert requests_response.json()["meta"]["total"] >= 1
