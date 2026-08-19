"""Route tests for the Jinja+HTMX trace UI (T231).

Requires PostgreSQL (see `tests/web/conftest.py`) — skipped locally
without one running, same as `tests/api`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.traces import TraceIngestPayload
from app.services.trace_service import ingest_trace
from tests.integration.conftest import requires_postgres
from tests.web.conftest import make_project

pytestmark = requires_postgres


def _ingest(db: Session, project_id: object, **overrides: object) -> None:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": "trace_ui_test",
        "name": "answer_question",
        "status": "success",
        "started_at": now,
        "ended_at": now,
        "spans": [
            {
                "id": "span_root",
                "name": "answer_question",
                "kind": "chain",
                "status": "success",
                "started_at": now,
                "ended_at": now,
            },
            {
                "id": "span_llm",
                "parent_span_id": "span_root",
                "name": "generate",
                "kind": "llm",
                "status": "success",
                "started_at": now,
                "ended_at": now,
                "provider": "openai",
                "model": "gpt-4o-mini",
                "input_tokens": 100,
                "output_tokens": 50,
            },
            {
                "id": "span_orphan",
                "parent_span_id": "span_never_sent",
                "name": "orphaned_step",
                "kind": "tool",
                "status": "success",
                "started_at": now,
                "ended_at": now,
            },
        ],
    }
    defaults.update(overrides)
    payload = TraceIngestPayload.model_validate(defaults)
    ingest_trace(db, project_id, payload)


def test_traces_list_shows_onboarding_when_empty(web_client: TestClient) -> None:
    response = web_client.get("/traces")
    assert response.status_code == 200
    assert "No traces yet" in response.text
    assert "pip install" in response.text


def test_traces_list_shows_recorded_trace(web_client: TestClient, pg_session: Session) -> None:
    project = make_project(pg_session, name="UI Test App", slug="ui-test-app")
    _ingest(pg_session, project.id)

    response = web_client.get("/traces")

    assert response.status_code == 200
    assert "answer_question" in response.text
    assert "UI Test App" in response.text


def test_traces_list_filters_by_status(web_client: TestClient, pg_session: Session) -> None:
    project = make_project(pg_session, name="Filter App", slug="filter-app")
    _ingest(pg_session, project.id, id="trace_filter_test", status="error")

    match = web_client.get("/traces", params={"status": "error"})
    no_match = web_client.get("/traces", params={"status": "success"})

    assert "answer_question" in match.text
    assert "No traces match these filters" in no_match.text


def test_trace_detail_renders_waterfall_with_nesting_and_orphan(
    web_client: TestClient, pg_session: Session
) -> None:
    project = make_project(pg_session, name="Detail App", slug="detail-app")
    _ingest(pg_session, project.id, id="trace_detail_test")

    response = web_client.get("/traces/trace_detail_test")

    assert response.status_code == 200
    assert "generate" in response.text
    assert "orphaned_step" in response.text
    assert "orphan" in response.text  # orphan flag rendered
    assert "gpt-4o-mini" in response.text


def test_trace_detail_missing_trace_shows_not_found(web_client: TestClient) -> None:
    response = web_client.get("/traces/does_not_exist")
    assert response.status_code == 200
    assert "Trace not found" in response.text


def test_unauthenticated_request_redirects_to_login(pg_session: Session) -> None:
    from app.db.session import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: pg_session
    try:
        client = TestClient(app, follow_redirects=False)
        response = client.get("/traces")
        assert response.status_code == 303
        assert response.headers["location"].startswith("/login")
    finally:
        app.dependency_overrides.clear()
