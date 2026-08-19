# llm-lens

Decorator-based nested tracing SDK for [LLM Lens](../README.md). Trace any
Python code — LLM calls, tool calls, retrieval steps, whole agent chains —
and see the nested call tree in the LLM Lens UI, with zero server-side
dependencies pulled into your project (`httpx` only).

## Install

```bash
pip install ./sdk   # or, once published: pip install llm-lens
```

## Quickstart

```python
import llm_lens

llm_lens.configure(project="My App", base_url="http://localhost:8000")


@llm_lens.trace()
def answer_question(question: str) -> str:
    context = retrieve(question)
    return generate(question, context)


@llm_lens.span(kind="retriever")
def retrieve(question: str) -> str:
    return "...retrieved context..."


@llm_lens.span(kind="llm")
def generate(question: str, context: str) -> str:
    # call your LLM provider here, then report usage:
    llm_lens.set_usage(
        provider="openai", model="gpt-4o-mini", input_tokens=120, output_tokens=42
    )
    return "...answer..."


answer_question("What is LLM Lens?")
```

Open `http://localhost:8000/traces` — the call above shows up as a trace
named `answer_question` with two nested spans (`retrieve`, `generate`),
timings, and the LLM span's token usage/cost.

## Configuration

```python
llm_lens.configure(
    project="My App",       # OR api_key="llk_..." for precise project attribution
    api_key=None,
    base_url="http://localhost:8000",
    flush_interval_seconds=2.0,
    max_queue_size=10_000,
)
```

- Provide **either** `project` (a human-readable name, auto-created/resolved
  server-side) **or** `api_key` (a project-scoped key from the LLM Lens UI).
- If `configure()` is never called, `@trace`/`@span` run your function
  directly with no overhead and no network calls (safe to leave decorators
  in code that runs outside an LLM Lens environment, e.g. CI).
- If the server is unreachable, tracing fails silently — your application's
  behavior and return values are never affected.

## API

- `@llm_lens.trace(name=None)` — starts a new top-level trace; ends it when
  the function returns or raises.
- `@llm_lens.span(name=None, kind="custom")` — starts a nested span under
  whatever trace/span is active in the current context. `kind` is one of
  `llm`, `tool`, `retriever`, `embedding`, `chain`, `agent`, `custom`.
- `llm_lens.set_usage(provider=, model=, input_tokens=, output_tokens=)` —
  attach LLM usage fields to the currently executing span; the server
  computes cost using the same pricing rules as gateway-captured requests.

Both decorators support `async def` functions transparently.
