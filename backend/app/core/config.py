"""Application configuration via pydantic-settings (constitution: all external
input, including environment configuration, validated via Pydantic).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = Field(default="LLM Lens", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="APP_DEBUG")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://llm_lens:llm_lens@localhost:5432/llm_lens",
        alias="DATABASE_URL",
    )

    # --- Admin auth (single-admin-cookie session, research.md §4) ---
    admin_email: str = Field(default="admin@example.com", alias="ADMIN_EMAIL")
    admin_password_hash: str = Field(default="", alias="ADMIN_PASSWORD_HASH")
    session_cookie_name: str = Field(default="llm_lens_session", alias="SESSION_COOKIE_NAME")
    session_max_age_seconds: int = Field(default=60 * 60 * 24 * 7, alias="SESSION_MAX_AGE_SECONDS")

    # --- CORS ---
    # NoDecode: env value is a plain comma-separated string, not JSON — skip
    # pydantic-settings' default JSON-decode-for-complex-types behavior so the
    # `_split_csv` validator below receives the raw string.
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ALLOW_ORIGINS",
    )

    # --- Privacy (constitution Principle II) ---
    store_prompts: bool = Field(default=False, alias="STORE_PROMPTS")
    store_responses: bool = Field(default=False, alias="STORE_RESPONSES")
    request_retention_days: int = Field(default=90, alias="REQUEST_RETENTION_DAYS")

    # --- Telemetry ingestion (LiteLLM callback -> backend webhook, T031/T032) ---
    # Shared secret the LiteLLM custom callback presents when POSTing telemetry
    # events; distinct from the admin session (service-to-service, not user auth).
    litellm_callback_token: str = Field(
        default="change-me-in-production", alias="LITELLM_CALLBACK_TOKEN"
    )

    # --- Pagination ---
    default_page_size: int = Field(default=20, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE")

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached `Settings` instance (single source of truth)."""

    return Settings()
