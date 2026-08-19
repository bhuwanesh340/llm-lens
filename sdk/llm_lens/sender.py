"""Background batching sender (T216).

Runs in a daemon thread so it never keeps the host process alive, and a
slow/unreachable server never blocks traced code (FR-213, FR-215). Every
network/HTTP error is swallowed here — by design, tracing failures must be
invisible to the host application.
"""

from __future__ import annotations

import atexit
import contextlib
import queue
import threading
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from llm_lens.config import ClientConfig

_INGEST_PATH = "/api/v1/traces/ingest"


class _Sender:
    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=config.max_queue_size)
        self._stop = threading.Event()
        self._client = httpx.Client(timeout=5.0)
        self._thread = threading.Thread(target=self._run, name="llm-lens-sender", daemon=True)
        self._thread.start()

    def enqueue(self, payload: dict[str, Any]) -> None:
        with contextlib.suppress(queue.Full):
            self._queue.put_nowait(payload)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers

    def _send_one(self, payload: dict[str, Any]) -> None:
        if self._config.project and not self._config.api_key:
            payload = {**payload, "project": self._config.project}
        with contextlib.suppress(Exception):
            self._client.post(
                f"{self._config.base_url}{_INGEST_PATH}",
                json=payload,
                headers=self._headers(),
            )

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                payload = self._queue.get(timeout=self._config.flush_interval_seconds)
            except queue.Empty:
                continue
            self._send_one(payload)

    def flush_and_stop(self) -> None:
        self._stop.set()
        while True:
            try:
                payload = self._queue.get_nowait()
            except queue.Empty:
                break
            self._send_one(payload)
        with contextlib.suppress(Exception):
            self._client.close()


_sender: _Sender | None = None
_lock = threading.Lock()


def restart_sender(config: ClientConfig) -> None:
    """(Re)start the background sender for a new `configure()` call."""

    global _sender
    with _lock:
        previous = _sender
        _sender = _Sender(config)
        if previous is not None:
            previous.flush_and_stop()


def enqueue(payload: dict[str, Any]) -> None:
    sender = _sender
    if sender is not None:
        sender.enqueue(payload)


def _atexit_flush() -> None:
    sender = _sender
    if sender is not None:
        sender.flush_and_stop()


atexit.register(_atexit_flush)
