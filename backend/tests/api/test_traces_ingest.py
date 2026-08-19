"""API tests for project API keys + trace ingestion (T212).

Requires Postgres (see conftest) — skipped locally without one running,
same as the rest of `tests/api`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.api_key_service import generate_api_key
from tests.api.conftest import make_project


def _trace_payload(**overrides: object) -> dict[object, object]:
    now = datetime.now(UTC).isoformat()
    payload: dict[object, object] = {
        "id": "trace_abc123",
        "name": "answer_question",
        "status": "success",
        "started_at": now,
        "spans": [
            {
                "id": "span_root",
                "name": "answer_question",
                "kind": "chain",
                "status": "success",
                "started_at": now,
            },
            {
                "id": "span_llm",
                "parent_span_id": "span_root",
                "name": "generate",
                "kind": "llm",
                "status": "success",
                "started_at": now,
                "provider": "openai",
                "model": "gpt-4o-mini",
                "input_tokens": 100,
                "output_tokens": 50,
            },
        ],
    }
    payload.update(overrides)
    return payload


def test_ingest_with_valid_key_persists_trace(
    api_client: TestClient, pg_session: Session
) -> None:
    project = make_project(pg_session, name="Ingest App", slug="ingest-app")
    created = generate_api_key(pg_session, project.id, "ci-key")

    response = api_client.post(
        "/api/v1/traces/ingest",
        json=_trace_payload(),
        headers={"Authorization": f"Bearer {created.plaintext}"},
    )

    assert response.status_code == 201
    assert response.json()["trace_id"] == "trace_abc123"


def test_ingest_with_invalid_key_is_rejected(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/traces/ingest",
        json=_trace_payload(id="trace_def456"),
        headers={"Authorization": "Bearer llk_not_a_real_key"},
    )

    assert response.status_code == 401


def test_ingest_with_shared_token_and_project_name_resolves_project(
    api_client: TestClient, pg_session: Session
) -> None:
    token = get_settings().litellm_callback_token

    response = api_client.post(
        "/api/v1/traces/ingest",
        json=_trace_payload(id="trace_name_only", project="Name Only App"),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201


def test_ingest_with_revoked_key_is_rejected(
    api_client: TestClient, pg_session: Session
) -> None:
    project = make_project(pg_session, name="Revoke App", slug="revoke-app")
    created = generate_api_key(pg_session, project.id, "revoked-key")
    api_client.delete(f"/api/v1/keys/{created.api_key.id}")

    response = api_client.post(
        "/api/v1/traces/ingest",
        json=_trace_payload(id="trace_ghi789"),
        headers={"Authorization": f"Bearer {created.plaintext}"},
    )

    assert response.status_code == 401


def test_key_lifecycle_create_list_revoke(api_client: TestClient, pg_session: Session) -> None:
    project = make_project(pg_session, name="Keys App", slug="keys-app")

    create_resp = api_client.post(
        f"/api/v1/projects/{project.id}/keys", json={"name": "prod"}
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["key"].startswith("llk_")
    key_id = body["id"]

    list_resp = api_client.get(f"/api/v1/projects/{project.id}/keys")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert "key" not in list_resp.json()[0]

    revoke_resp = api_client.delete(f"/api/v1/keys/{key_id}")
    assert revoke_resp.status_code == 204
