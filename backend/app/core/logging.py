"""Structured logging setup using structlog.

Constitution requirement: logs MUST NOT include secrets, prompts, or
response content. This module configures a processor pipeline that emits
JSON in production and a readable console format in development, and
provides a `get_logger` helper used throughout the codebase.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, cast

import structlog

from app.core.config import get_settings

_REDACTED = "***REDACTED***"
_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "admin_password_hash",
    "secret_key",
    "authorization",
    "api_key",
    "key_hash",
    "token",
    "cookie",
    "prompt",
    "response",
}


def _redact_sensitive(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Processor that redacts known-sensitive keys from every log event."""

    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = _REDACTED
    return event_dict


def configure_logging() -> None:
    """Configure structlog + stdlib logging once at process startup."""

    settings = get_settings()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _redact_sensitive,
    ]

    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.debug
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger for the given module name."""

    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
