"""Integration test fixtures (T024): require a real PostgreSQL instance
(JSONB support needed for `LLMRequest.metadata_`). Set
`LLM_LENS_TEST_DATABASE_URL` to point at one (e.g. the `postgres` service
from docker-compose); tests are skipped if it is not reachable.
"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base

TEST_DATABASE_URL = os.environ.get(
    "LLM_LENS_TEST_DATABASE_URL",
    "postgresql+psycopg://llm_lens:llm_lens@localhost:5432/llm_lens_test",
)


def _postgres_reachable() -> bool:
    try:
        engine = create_engine(
            TEST_DATABASE_URL, future=True, connect_args={"connect_timeout": 2}
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:  # noqa: BLE001
        return False


requires_postgres = pytest.mark.skipif(
    not _postgres_reachable(), reason="Integration tests require a reachable PostgreSQL instance"
)


@pytest.fixture()
def pg_session() -> Generator[Session, None, None]:
    engine = create_engine(
        TEST_DATABASE_URL, future=True, connect_args={"connect_timeout": 2}
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
