"""Decorator API: `@trace`, `@span`, `set_usage` (T217, T218, T219).

Both decorators support plain and `async def` functions transparently.
Nesting is entirely automatic via `llm_lens.context` — callers never pass
trace/span ids by hand (FR-210, FR-211).
"""

from __future__ import annotations

import functools
import inspect
import threading
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypeVar, cast

from llm_lens.config import is_configured
from llm_lens.context import (
    get_current_span_id,
    get_current_trace,
    reset_current_span_id,
    reset_current_trace,
    set_current_span_id,
    set_current_trace,
)
from llm_lens.sender import enqueue

F = TypeVar("F", bound=Callable[..., Any])


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass
class _SpanRecord:
    id: str
    parent_span_id: str | None
    name: str
    kind: str
    status: str = "running"
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    provider: str | None = None
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_type: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind,
            "status": self.status,
            "started_at": _iso(self.started_at),
            "ended_at": _iso(self.ended_at),
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class TraceBuilder:
    """Accumulates a trace's spans in memory; sent as one batch on completion."""

    def __init__(self, trace_id: str, name: str, environment: str | None = None) -> None:
        self.id = trace_id
        self.name = name
        self.status = "running"
        self.started_at = datetime.now(UTC)
        self.ended_at: datetime | None = None
        self.environment = environment
        self.metadata: dict[str, object] = {}
        self.spans: dict[str, _SpanRecord] = {}
        self._lock = threading.Lock()

    def start_span(self, span_id: str, parent_span_id: str | None, name: str, kind: str) -> None:
        record = _SpanRecord(id=span_id, parent_span_id=parent_span_id, name=name, kind=kind)
        with self._lock:
            self.spans[span_id] = record

    def end_span(self, span_id: str, status: str, error: BaseException | None = None) -> None:
        with self._lock:
            record = self.spans.get(span_id)
            if record is None:
                return
            record.ended_at = datetime.now(UTC)
            record.status = status
            if error is not None:
                record.error_type = type(error).__name__
                record.error_message = str(error)

    def mark_error_ancestors(self, span_id: str) -> None:
        """FR-205: an error propagates up to every ancestor span."""

        with self._lock:
            seen: set[str] = set()
            current = self.spans.get(span_id)
            while current is not None and current.parent_span_id is not None:
                parent_id = current.parent_span_id
                if parent_id in seen:
                    break
                seen.add(parent_id)
                parent = self.spans.get(parent_id)
                if parent is None:
                    break
                parent.status = "error"
                current = parent

    def set_usage(
        self, span_id: str, *, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> None:
        with self._lock:
            record = self.spans.get(span_id)
            if record is None:
                return
            record.kind = "llm"
            record.provider = provider
            record.model = model
            record.input_tokens = input_tokens
            record.output_tokens = output_tokens

    def finish(self, status: str) -> None:
        self.status = status
        self.ended_at = datetime.now(UTC)

    def to_payload(self) -> dict[str, object]:
        with self._lock:
            spans = [record.to_payload() for record in self.spans.values()]
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "started_at": _iso(self.started_at),
            "ended_at": _iso(self.ended_at),
            "environment": self.environment,
            "metadata": self.metadata,
            "spans": spans,
        }


def trace(name: str | None = None) -> Callable[[F], F]:
    """FR-210: start a new top-level `Trace` for a function; end it when the
    function returns or raises. No-ops (zero overhead) when the SDK has
    never been `configure()`d (FR-215)."""

    def decorator(func: F) -> F:
        trace_name = name or func.__name__

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if not is_configured():
                    return await cast(Callable[..., Awaitable[Any]], func)(*args, **kwargs)
                builder = TraceBuilder(_new_id("trace"), trace_name)
                trace_token = set_current_trace(builder)
                span_token = set_current_span_id(None)
                try:
                    result = await cast(Callable[..., Awaitable[Any]], func)(*args, **kwargs)
                except BaseException:
                    builder.finish("error")
                    raise
                else:
                    builder.finish("success")
                    return result
                finally:
                    reset_current_span_id(span_token)
                    reset_current_trace(trace_token)
                    enqueue(builder.to_payload())

            return cast(F, async_wrapper)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not is_configured():
                return func(*args, **kwargs)
            builder = TraceBuilder(_new_id("trace"), trace_name)
            trace_token = set_current_trace(builder)
            span_token = set_current_span_id(None)
            try:
                result = func(*args, **kwargs)
            except BaseException:
                builder.finish("error")
                raise
            else:
                builder.finish("success")
                return result
            finally:
                reset_current_span_id(span_token)
                reset_current_trace(trace_token)
                enqueue(builder.to_payload())

        return cast(F, sync_wrapper)

    return decorator


def span(name: str | None = None, kind: str = "custom") -> Callable[[F], F]:
    """FR-211: start a nested `Span` under whatever trace/span is currently
    active in this context. If no `@trace` is active, a bare `@span` becomes
    its own single-span trace rather than silently dropping the call."""

    def decorator(func: F) -> F:
        span_name = name or func.__name__

        def _enter() -> tuple[TraceBuilder, bool, Any, str, Any]:
            builder = get_current_trace()
            owns_trace = builder is None
            trace_token = None
            if builder is None:
                builder = TraceBuilder(_new_id("trace"), span_name)
                trace_token = set_current_trace(builder)
            parent_span_id = get_current_span_id()
            span_id = _new_id("span")
            span_token = set_current_span_id(span_id)
            builder.start_span(span_id, parent_span_id, span_name, kind)
            return builder, owns_trace, trace_token, span_id, span_token

        def _exit_success(
            builder: TraceBuilder, owns_trace: bool, trace_token: Any, span_id: str, span_token: Any
        ) -> None:
            builder.end_span(span_id, "success")
            reset_current_span_id(span_token)
            if owns_trace:
                builder.finish("success")
                reset_current_trace(trace_token)
                enqueue(builder.to_payload())

        def _exit_error(
            builder: TraceBuilder,
            owns_trace: bool,
            trace_token: Any,
            span_id: str,
            span_token: Any,
            exc: BaseException,
        ) -> None:
            builder.end_span(span_id, "error", error=exc)
            builder.mark_error_ancestors(span_id)
            reset_current_span_id(span_token)
            if owns_trace:
                builder.finish("error")
                reset_current_trace(trace_token)
                enqueue(builder.to_payload())

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if not is_configured():
                    return await cast(Callable[..., Awaitable[Any]], func)(*args, **kwargs)
                builder, owns_trace, trace_token, span_id, span_token = _enter()
                try:
                    result = await cast(Callable[..., Awaitable[Any]], func)(*args, **kwargs)
                except BaseException as exc:
                    _exit_error(builder, owns_trace, trace_token, span_id, span_token, exc)
                    raise
                _exit_success(builder, owns_trace, trace_token, span_id, span_token)
                return result

            return cast(F, async_wrapper)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not is_configured():
                return func(*args, **kwargs)
            builder, owns_trace, trace_token, span_id, span_token = _enter()
            try:
                result = func(*args, **kwargs)
            except BaseException as exc:
                _exit_error(builder, owns_trace, trace_token, span_id, span_token, exc)
                raise
            _exit_success(builder, owns_trace, trace_token, span_id, span_token)
            return result

        return cast(F, sync_wrapper)

    return decorator


def set_usage(
    *, provider: str, model: str, input_tokens: int, output_tokens: int
) -> None:
    """FR-212: attach LLM fields to the span currently executing. No-ops
    outside of a `@span`/`@trace` call or when unconfigured."""

    builder = get_current_trace()
    span_id = get_current_span_id()
    if builder is None or span_id is None:
        return
    builder.set_usage(
        span_id,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
