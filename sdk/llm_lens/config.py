"""Module-level SDK configuration (T215).

`configure()` is the SDK's only required setup call. Until it is called,
every decorator in `tracing.py` runs in no-op passthrough mode (FR-215) —
this is what lets a host application safely import and use `llm_lens`
even in environments (CI, offline dev) where no server is reachable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClientConfig:
    project: str | None
    api_key: str | None
    base_url: str
    flush_interval_seconds: float
    max_queue_size: int


_config: ClientConfig | None = None


def configure(
    *,
    project: str | None = None,
    api_key: str | None = None,
    base_url: str = "http://localhost:8000",
    flush_interval_seconds: float = 2.0,
    max_queue_size: int = 10_000,
) -> None:
    """Configure the SDK for the current process.

    Either `project` (a human-readable name, auto-created/resolved server-side
    per feature 002) or `api_key` (a project-scoped `llk_...` key, feature 003)
    must be provided so ingested traces can be attributed (FR-214).
    """

    global _config
    if not project and not api_key:
        raise ValueError("configure() requires either project= or api_key=")
    _config = ClientConfig(
        project=project,
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        flush_interval_seconds=flush_interval_seconds,
        max_queue_size=max_queue_size,
    )
    # (Re)start the sender against the new config — imported lazily to avoid
    # a hard import cycle at module load time.
    from llm_lens.sender import restart_sender

    restart_sender(_config)


def get_config() -> ClientConfig | None:
    return _config


def is_configured() -> bool:
    return _config is not None
