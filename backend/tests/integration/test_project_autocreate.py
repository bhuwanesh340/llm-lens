"""Integration tests for project auto-creation on first trace (T115).

Covers FR-102 (auto-create), FR-103 (case/whitespace equivalence), and
FR-105 (concurrent same-name traces collapse to exactly one project).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.project import Project
from app.services.project_service import resolve_or_create_project
from tests.integration.conftest import requires_postgres

pytestmark = requires_postgres


def _project_count(db: Session, slug: str) -> int:
    return db.execute(
        select(func.count()).select_from(Project).where(Project.slug == slug)
    ).scalar_one()


def test_first_trace_creates_project(pg_session: Session) -> None:
    project = resolve_or_create_project(pg_session, "Brand New App")
    pg_session.commit()

    assert project.slug == "brand-new-app"
    assert project.name == "Brand New App"
    assert project.auto_created is True


def test_second_trace_reuses_existing_project(pg_session: Session) -> None:
    first = resolve_or_create_project(pg_session, "Repeat App")
    pg_session.commit()
    second = resolve_or_create_project(pg_session, "Repeat App")
    pg_session.commit()

    assert first.id == second.id
    assert _project_count(pg_session, "repeat-app") == 1


def test_name_variants_resolve_to_one_project(pg_session: Session) -> None:
    """FR-103: case and whitespace differences must not fork the project."""

    ids = set()
    for variant in ["Support Bot", "support bot", "  SUPPORT   BOT  ", "support-bot"]:
        ids.add(resolve_or_create_project(pg_session, variant).id)
        pg_session.commit()

    assert len(ids) == 1
    assert _project_count(pg_session, "support-bot") == 1


def test_concurrent_same_name_creates_exactly_one(pg_session: Session) -> None:
    """FR-105: a racing insert is absorbed via SAVEPOINT, not lost."""

    other = Session(bind=pg_session.get_bind())
    try:
        # Simulate the race: another transaction commits the same slug first.
        other.add(Project(name="Racy App", slug="racy-app", auto_created=True))
        other.commit()

        resolved = resolve_or_create_project(pg_session, "Racy App")
        pg_session.commit()

        assert resolved.slug == "racy-app"
        assert _project_count(pg_session, "racy-app") == 1
    finally:
        other.close()
