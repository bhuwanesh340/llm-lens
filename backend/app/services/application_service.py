"""Application CRUD service (T056, US4).

Attribution aggregation with the "unassigned" bucket lives in
`analytics_service.get_costs_by_application` / `usage_service` (grouping by
`application_id`, `None` → `"unassigned"`) — this module only owns the
`applications` table's own CRUD lifecycle.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.application import Application
from app.schemas.applications import ApplicationCreate, ApplicationUpdate


class DuplicateSlugError(Exception):
    def __init__(self, slug: str) -> None:
        super().__init__(f"An application with slug '{slug}' already exists")
        self.slug = slug


def list_applications(db: Session) -> list[Application]:
    return list(db.execute(select(Application).order_by(Application.name)).scalars().all())


def get_application(db: Session, application_id: uuid.UUID) -> Application | None:
    return db.get(Application, application_id)


def create_application(db: Session, payload: ApplicationCreate) -> Application:
    app = Application(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        environment=payload.environment,
    )
    db.add(app)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateSlugError(payload.slug) from exc
    db.refresh(app)
    return app


def update_application(
    db: Session, application_id: uuid.UUID, payload: ApplicationUpdate
) -> Application | None:
    app = get_application(db, application_id)
    if app is None:
        return None
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(app, field, value)
    db.commit()
    db.refresh(app)
    return app


def delete_application(db: Session, application_id: uuid.UUID) -> bool:
    app = get_application(db, application_id)
    if app is None:
        return False
    db.delete(app)
    db.commit()
    return True
