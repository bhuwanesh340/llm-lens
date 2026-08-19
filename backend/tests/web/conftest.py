"""Shared fixtures for web (Jinja+HTMX) UI tests (T231).

Requires PostgreSQL (see `tests/integration/conftest.py`), same as the
`tests/api` suite. Overrides `require_admin_page_session` (page auth)
rather than `require_admin_session` (JSON API auth) — the two are
intentionally separate dependencies (see `app/web/deps.py`).
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.web.deps import require_admin_page_session
from tests.api.conftest import make_project  # noqa: F401
from tests.integration.conftest import pg_session, requires_postgres  # noqa: F401

__all__ = ["requires_postgres", "pg_session", "web_client", "make_project"]


@pytest.fixture()
def web_client(pg_session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: pg_session
    app.dependency_overrides[require_admin_page_session] = lambda: "admin@example.com"
    try:
        yield TestClient(app, follow_redirects=False)
    finally:
        app.dependency_overrides.clear()
