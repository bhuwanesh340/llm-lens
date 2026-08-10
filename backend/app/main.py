"""FastAPI application entrypoint (T015, T020)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import mount_metrics
from app.services.query_filters import InvalidFilterError

configure_logging()
logger = get_logger(__name__)

settings = get_settings()

app = FastAPI(
    title="LLM Lens API",
    version="0.1.0",
    description="Self-hosted LLM observability platform — analytics control plane.",
)

# CORS: configurable origin allowlist (constitution Principle VI).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mount_metrics(app)
app.include_router(api_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Wrap all HTTPExceptions in the error envelope from contracts/api.md.

    `exc.detail` may be a plain string (existing endpoints) or a
    `{"code": ..., "message": ...}` dict (new Phase 4+ endpoints); both are
    normalized to `{"error": {"code", "message", "request_id"}}`.
    """

    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        code, message = str(detail["code"]), str(detail["message"])
    else:
        code, message = "HTTP_ERROR", str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request.headers.get("x-request-id"),
            }
        },
        headers=exc.headers,
    )


@app.exception_handler(InvalidFilterError)
async def invalid_filter_handler(request: Request, exc: InvalidFilterError) -> JSONResponse:
    """Malformed query filters (bad date range/UUID) → 400 (FR per contracts/api.md)."""

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_FILTER",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id"),
            }
        },
    )


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("startup", app_env=settings.app_env)
