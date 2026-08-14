"""Project CRUD (T107) and name-based resolution (T116).

Attribution aggregation with the "unassigned" bucket lives in
`analytics_service` / `usage_service` (grouping by `project_id`, `None` →
`"unassigned"`) — this module owns the `projects` table lifecycle and the
name → project resolution used by telemetry ingestion.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.project import Project
from app.schemas.projects import PROJECT_NAME_MAX_LENGTH, ProjectCreate, ProjectUpdate

_SLUG_INVALID = re.compile(r"[^a-z0-9]+")


class DuplicateSlugError(Exception):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A project with slug '{slug}' already exists")
        self.slug = slug


class InvalidProjectNameError(Exception):
    """Raised for empty, whitespace-only, over-length, or unsluggable names (FR-107)."""


def normalize_project_name(name: str) -> str:
    """Collapse internal whitespace and trim, preserving the caller's casing."""

    normalized = " ".join(name.split())
    if not normalized:
        raise InvalidProjectNameError("Project name must not be empty or whitespace-only")
    if len(normalized) > PROJECT_NAME_MAX_LENGTH:
        raise InvalidProjectNameError(
            f"Project name must be at most {PROJECT_NAME_MAX_LENGTH} characters"
        )
    return normalized


def derive_slug(name: str) -> str:
    """Derive the canonical lookup key, so names differing only by case or
    whitespace resolve to the same project (FR-103)."""

    slug = _SLUG_INVALID.sub("-", name.casefold()).strip("-")
    if not slug:
        raise InvalidProjectNameError(
            f"Project name '{name}' contains no alphanumeric characters"
        )
    return slug[:128]


def list_projects(db: Session) -> list[Project]:
    return list(db.execute(select(Project).order_by(Project.name)).scalars().all())


def get_project(db: Session, project_id: uuid.UUID) -> Project | None:
    return db.get(Project, project_id)


def get_project_by_slug(db: Session, slug: str) -> Project | None:
    return db.execute(select(Project).where(Project.slug == slug)).scalar_one_or_none()


def create_project(db: Session, payload: ProjectCreate) -> Project:
    name = normalize_project_name(payload.name)
    slug = payload.slug or derive_slug(name)
    project = Project(
        name=name,
        slug=slug,
        description=payload.description,
        environment=payload.environment,
        auto_created=False,
    )
    db.add(project)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateSlugError(slug) from exc
    db.refresh(project)
    return project


def resolve_or_create_project(db: Session, name: str) -> Project:
    """Return the project for `name`, creating it on first sight (FR-102).

    Concurrent callers using the same name collapse onto one row: the insert
    runs in a SAVEPOINT so a unique-violation can be rolled back and re-read
    without discarding the caller's surrounding transaction (FR-105).
    """

    normalized = normalize_project_name(name)
    slug = derive_slug(normalized)

    existing = get_project_by_slug(db, slug)
    if existing is not None:
        return existing

    project = Project(name=normalized, slug=slug, auto_created=True)
    try:
        with db.begin_nested():
            db.add(project)
        return project
    except IntegrityError:
        # Another transaction inserted the same slug first — adopt theirs.
        raced = get_project_by_slug(db, slug)
        if raced is None:  # pragma: no cover - unique violation implies a row exists
            raise
        return raced


def update_project(
    db: Session, project_id: uuid.UUID, payload: ProjectUpdate
) -> Project | None:
    project = get_project(db, project_id)
    if project is None:
        return None
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] is not None:
        updates["name"] = normalize_project_name(updates["name"])
    for field, value in updates.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: uuid.UUID) -> bool:
    project = get_project(db, project_id)
    if project is None:
        return False
    db.delete(project)
    db.commit()
    return True
