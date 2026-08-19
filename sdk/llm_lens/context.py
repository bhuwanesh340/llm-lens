"""Context propagation for nested trace/span stacks (T214).

Uses `contextvars.ContextVar` (not thread-locals) so nesting is correct
across both plain threads and `asyncio` tasks — each gets an independent
copy of the context, and a child span created inside a task automatically
sees its caller's trace/span as its parent (FR-210, FR-211), with no
manual id-passing required from the host application.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llm_lens.tracing import TraceBuilder

_current_trace: ContextVar[TraceBuilder | None] = ContextVar(
    "llm_lens_current_trace", default=None
)
_current_span_id: ContextVar[str | None] = ContextVar("llm_lens_current_span_id", default=None)


def get_current_trace() -> TraceBuilder | None:
    return _current_trace.get()


def get_current_span_id() -> str | None:
    return _current_span_id.get()


def set_current_trace(builder: TraceBuilder | None) -> Token[TraceBuilder | None]:
    return _current_trace.set(builder)


def reset_current_trace(token: Token[TraceBuilder | None]) -> None:
    _current_trace.reset(token)


def set_current_span_id(span_id: str | None) -> Token[str | None]:
    return _current_span_id.set(span_id)


def reset_current_span_id(token: Token[str | None]) -> None:
    _current_span_id.reset(token)
