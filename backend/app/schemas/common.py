"""Common Pydantic schemas: pagination envelope, error envelope (T017)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class Page(BaseModel, Generic[T]):
    """Standard paginated list envelope used by every list endpoint."""

    items: list[T]
    meta: PageMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    """Matches the error envelope documented in contracts/api.md."""

    error: ErrorDetail
