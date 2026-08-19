"""Shared Jinja2 environment for the server-rendered UI (T223)."""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.web.filters import filters_query_string

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["filters_qs"] = filters_query_string
