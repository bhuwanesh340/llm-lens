"""Shared pytest fixtures.

Unit tests (T022) that need a DB session use an in-memory SQLite engine
scoped to just the `providers`/`models` tables (the only tables touched by
the pricing/cost registry) — this avoids SQLite's lack of a native JSONB
type, which `LLMRequest.metadata_` requires and which integration tests
(T024) exercise against a real PostgreSQL instance instead.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.model import Model
from app.db.models.provider import Provider


@pytest.fixture()
def pricing_db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine, tables=[Provider.__table__, Model.__table__])
    session_factory = sessionmaker(bind=engine, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
