from __future__ import annotations

import pytest

import llm_lens.tracing as tracing_module
from llm_lens.tracing import set_usage, span, trace


@pytest.fixture(autouse=True)
def configured(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    monkeypatch.setattr(tracing_module, "is_configured", lambda: True)
    sent: list[dict[str, object]] = []
    monkeypatch.setattr(tracing_module, "enqueue", sent.append)
    return sent


def test_noop_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tracing_module, "is_configured", lambda: False)
    calls: list[int] = []

    @trace()
    def work() -> int:
        calls.append(1)
        return 42

    assert work() == 42
    assert calls == [1]


def test_trace_produces_nested_spans_in_call_order(
    configured: list[dict[str, object]],
) -> None:
    @span(kind="tool")
    def fetch() -> str:
        return "data"

    @span(kind="llm")
    def generate() -> str:
        set_usage(provider="openai", model="gpt-4o-mini", input_tokens=10, output_tokens=5)
        return "answer"

    @trace(name="pipeline")
    def run() -> str:
        fetch()
        return generate()

    assert run() == "answer"
    assert len(configured) == 1

    payload = configured[0]
    assert payload["name"] == "pipeline"
    assert payload["status"] == "success"
    spans = payload["spans"]
    assert isinstance(spans, list)
    assert len(spans) == 2
    assert {s["kind"] for s in spans} == {"tool", "llm"}
    llm_span = next(s for s in spans if s["kind"] == "llm")
    assert llm_span["provider"] == "openai"
    assert llm_span["model"] == "gpt-4o-mini"
    assert llm_span["input_tokens"] == 10
    assert llm_span["output_tokens"] == 5
    # both spans are direct children of the trace itself (no span wraps `run`)
    assert all(s["parent_span_id"] is None for s in spans)


def test_span_without_active_trace_becomes_its_own_trace(
    configured: list[dict[str, object]],
) -> None:
    @span(kind="tool")
    def standalone() -> str:
        return "ok"

    assert standalone() == "ok"
    assert len(configured) == 1
    spans = configured[0]["spans"]
    assert isinstance(spans, list)
    assert len(spans) == 1


def test_nested_span_records_parent_child_relationship(
    configured: list[dict[str, object]],
) -> None:
    @span(kind="llm")
    def inner() -> None:
        pass

    @span(kind="chain")
    def outer() -> None:
        inner()

    @trace()
    def run() -> None:
        outer()

    run()
    spans = configured[0]["spans"]
    assert isinstance(spans, list)
    by_kind = {s["kind"]: s for s in spans}
    assert by_kind["llm"]["parent_span_id"] == by_kind["chain"]["id"]


def test_exception_marks_span_and_ancestors_as_error(
    configured: list[dict[str, object]],
) -> None:
    @span(kind="tool")
    def failing() -> None:
        raise ValueError("boom")

    @span(kind="chain")
    def middle() -> None:
        failing()

    @trace()
    def run() -> None:
        middle()

    with pytest.raises(ValueError):
        run()

    payload = configured[0]
    assert payload["status"] == "error"
    statuses = {s["name"]: s["status"] for s in payload["spans"]}
    assert statuses["failing"] == "error"
    assert statuses["middle"] == "error"  # FR-205: propagated to the ancestor


def test_exception_does_not_discard_already_recorded_sibling_spans(
    configured: list[dict[str, object]],
) -> None:
    @span(kind="tool")
    def first() -> str:
        return "ok"

    @span(kind="tool")
    def second() -> None:
        raise RuntimeError("boom")

    @trace()
    def run() -> None:
        first()
        second()

    with pytest.raises(RuntimeError):
        run()

    spans = configured[0]["spans"]
    assert isinstance(spans, list)
    statuses = {s["name"]: s["status"] for s in spans}
    assert statuses == {"first": "success", "second": "error"}


async def _async_flow() -> str:
    @span(kind="llm")
    async def generate() -> str:
        set_usage(provider="openai", model="gpt-4o-mini", input_tokens=1, output_tokens=1)
        return "answer"

    @trace()
    async def run() -> str:
        return await generate()

    return await run()


@pytest.mark.asyncio
async def test_async_decorators_produce_a_nested_trace(
    configured: list[dict[str, object]],
) -> None:
    assert await _async_flow() == "answer"
    assert len(configured) == 1
    spans = configured[0]["spans"]
    assert isinstance(spans, list)
    assert spans[0]["kind"] == "llm"
