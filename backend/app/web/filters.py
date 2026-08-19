"""Shared helpers for the Jinja web UI (T240) — building filter query strings
so tab/pagination links can round-trip the currently applied RangeFilters.
"""

from __future__ import annotations

from urllib.parse import urlencode

from app.api.deps import RangeFilters


def filters_query_string(filters: RangeFilters) -> str:
    params: dict[str, str] = {}
    if filters.date_from is not None:
        params["from"] = filters.date_from.isoformat()
    if filters.date_to is not None:
        params["to"] = filters.date_to.isoformat()
    if filters.provider:
        params["provider"] = filters.provider
    if filters.model:
        params["model"] = filters.model
    if filters.project_id:
        params["project_id"] = filters.project_id
    if filters.environment:
        params["environment"] = filters.environment
    return urlencode(params)
