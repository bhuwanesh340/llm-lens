"""FastAPI application entrypoint (T015, T020)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import mount_metrics

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


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("startup", app_env=settings.app_env)
