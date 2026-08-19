"""Package root — public API surface for `import llm_lens`."""

from __future__ import annotations

from llm_lens.config import configure
from llm_lens.tracing import set_usage, span, trace

__all__ = ["configure", "trace", "span", "set_usage"]

__version__ = "0.1.0"
