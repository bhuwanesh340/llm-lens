"""Manual smoke test: exercise the SDK against a locally running backend.

Run with: uv run --with ./llm-lens-project/llm-lens/sdk python smoke_test.py
(or, simpler, from within sdk/: `uv run python smoke_test.py` after `uv sync`)
"""

from __future__ import annotations

import time

import llm_lens

llm_lens.configure(
    project="Smoke Test App",
    base_url="http://127.0.0.1:8000",
    flush_interval_seconds=0.5,
)


@llm_lens.span(name="fetch_docs", kind="retriever")
def fetch_docs(query: str) -> list[str]:
    time.sleep(0.05)
    return [f"doc about {query}"]


@llm_lens.span(name="call_llm", kind="llm")
def call_llm(prompt: str) -> str:
    time.sleep(0.1)
    llm_lens.set_usage(
        provider="openai", model="gpt-4o-mini", input_tokens=120, output_tokens=45
    )
    return f"answer to: {prompt}"


@llm_lens.trace(name="answer_question")
def answer_question(question: str) -> str:
    docs = fetch_docs(question)
    return call_llm(f"{question} | context={docs}")


@llm_lens.trace(name="answer_question_with_error")
def answer_question_with_error(question: str) -> str:
    fetch_docs(question)
    raise RuntimeError("simulated downstream failure")


if __name__ == "__main__":
    print(answer_question("What is LLM Lens?"))
    try:
        answer_question_with_error("This one will fail")
    except RuntimeError as exc:
        print(f"caught expected error: {exc}")

    # Give the background sender a moment to flush before the script exits.
    time.sleep(2)
    print("done — check http://127.0.0.1:8000/traces")
