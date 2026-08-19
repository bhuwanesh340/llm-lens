"""Unit tests for trace/span ingestion (T211).

Uses a lightweight in-memory SQLite session directly against the service
functions -- these do not touch dialect-specific SQL (the `Trace`/`Span`
models are dialect-agnostic JSON, per FR-201/FR-202), so no Postgres is
required here, unlike most of this test suite.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.project import Project
from app.db.models.span import Span
from app.db.models.trace import Trace
from app.schemas.traces import TraceIngestPayload, TraceIngestSpan
from app.services.trace_service import ingest_trace


@pytest.fixture()
def sqlite_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _payload(**overrides: object) -> TraceIngestPayload:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": f"trace_{uuid.uuid4().hex}",
        "name": "answer_question",
        "status": "success",
        "started_at": now,
        "spans": [],
    }
    defaults.update(overrides)
    return TraceIngestPayload.model_validate(defaults)


def _span(**overrides: object) -> TraceIngestSpan:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": f"span_{uuid.uuid4().hex}",
        "name": "step",
        "kind": "custom",
        "status": "success",
        "started_at": now,
    }
    defaults.update(overrides)
    return TraceIngestSpan.model_validate(defaults)


def test_ingest_persists_nested_span_tree(sqlite_session: Session) -> None:
    root = _span(name="root", kind="chain")
    child = _span(name="child_llm", kind="llm", parent_span_id=root.id)
    payload = _payload(spans=[root, child])

    ingest_trace(sqlite_session, None, payload)

    stored_trace = sqlite_session.get(Trace, payload.id)
    assert stored_trace is not None
    stored_child = sqlite_session.get(Span, child.id)
    assert stored_child is not None
    assert stored_child.parent_span_id == root.id


def test_duplicate_span_id_is_a_noop(sqlite_session: Session) -> None:
    span = _span()
    payload = _payload(spans=[span])

    ingest_trace(sqlite_session, None, payload)
    ingest_trace(sqlite_session, None, payload)  # simulates SDK retry

    count = sqlite_session.query(Span).filter(Span.id == span.id).count()
    assert count == 1


def test_orphan_span_does_not_raise(sqlite_session: Session) -> None:
    orphan = _span(parent_span_id="span_never_sent")
    payload = _payload(spans=[orphan])

    ingest_trace(sqlite_session, None, payload)  # must not raise (FR-207)

    stored = sqlite_session.get(Span, orphan.id)
    assert stored is not None
    assert stored.parent_span_id == "span_never_sent"


def test_ingest_attributes_trace_to_project(sqlite_session: Session) -> None:
    project = Project(name="My App", slug="my-app")
    sqlite_session.add(project)
    sqlite_session.commit()

    payload = _payload()
    ingest_trace(sqlite_session, project.id, payload)

    stored_trace = sqlite_session.get(Trace, payload.id)
    assert stored_trace is not None
    assert stored_trace.project_id == project.id
