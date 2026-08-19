from __future__ import annotations

from llm_lens.config import ClientConfig
from llm_lens.sender import _Sender


def _config(**overrides: object) -> ClientConfig:
    defaults: dict[str, object] = {
        "project": "demo",
        "api_key": None,
        "base_url": "http://127.0.0.1:1",  # nothing listens here
        "flush_interval_seconds": 0.05,
        "max_queue_size": 10,
    }
    defaults.update(overrides)
    return ClientConfig(**defaults)  # type: ignore[arg-type]


def test_send_one_swallows_unreachable_server() -> None:
    """FR-213/FR-215: an unreachable server must never raise into the caller."""

    sender = _Sender(_config())
    try:
        sender._send_one({"id": "trace_x"})
    finally:
        sender.flush_and_stop()


def test_enqueue_drops_silently_when_queue_is_full() -> None:
    sender = _Sender(_config(max_queue_size=1))
    try:
        sender._stop.set()  # stop the background thread from draining the queue
        sender.enqueue({"id": "1"})
        sender.enqueue({"id": "2"})  # queue full -> dropped, must not raise
    finally:
        sender.flush_and_stop()


def test_flush_and_stop_drains_remaining_queue_without_raising() -> None:
    sender = _Sender(_config())
    sender._stop.set()
    sender.enqueue({"id": "1"})
    sender.enqueue({"id": "2"})
    sender.flush_and_stop()  # must drain both without raising
