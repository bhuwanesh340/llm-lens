"""Prometheus metrics (constitution: observability of the observability
platform itself). Base HTTP metrics here; telemetry-specific counters are
added in Phase 8 (T065).
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

http_requests_total = Counter(
    "llm_lens_http_requests_total",
    "Total HTTP requests processed by the backend",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "llm_lens_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

telemetry_events_total = Counter(
    "llm_lens_telemetry_events_total",
    "Total telemetry events successfully recorded",
    ["provider", "status"],
)

telemetry_events_failed_total = Counter(
    "llm_lens_telemetry_events_failed_total",
    "Total telemetry events that failed to record",
    ["reason"],
)

db_query_duration_seconds = Histogram(
    "llm_lens_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records request count and latency for every HTTP request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        path = request.url.path
        http_requests_total.labels(
            method=request.method, path=path, status_code=response.status_code
        ).inc()
        http_request_duration_seconds.labels(method=request.method, path=path).observe(duration)
        return response


def mount_metrics(app: FastAPI) -> None:
    """Mount the `/metrics` Prometheus scrape endpoint and request middleware."""

    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
