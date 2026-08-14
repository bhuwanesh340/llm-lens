"""Schemas for `Project` CRUD (T106) and name-based tagging (T116)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Kept in sync with the `projects.name` / `projects.slug` column widths.
PROJECT_NAME_MAX_LENGTH = 128


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=PROJECT_NAME_MAX_LENGTH)
    # Derived from `name` when omitted, so callers never have to build one.
    slug: str | None = Field(
        default=None, min_length=1, max_length=128, pattern=r"^[a-z0-9][a-z0-9-]*$"
    )
    description: str | None = None
    environment: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=PROJECT_NAME_MAX_LENGTH)
    description: str | None = None
    environment: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    environment: str | None
    auto_created: bool
    created_at: datetime
    updated_at: datetime
