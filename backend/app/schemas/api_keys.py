"""Schemas for project API keys (T202) — feature 003 Phase 1.

`ApiKeyCreatedResponse` is the only response that ever carries the
plaintext key, returned exactly once at creation time (constitution
Principle II: raw keys are never persisted or retrievable again).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    project_id: UUID | None
    enabled: bool
    created_at: datetime
    last_used_at: datetime | None


class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str
