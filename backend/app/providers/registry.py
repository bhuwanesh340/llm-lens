"""Provider registry (T026).

Validates that a provider is known/enabled (constitution Principle I: all
provider configuration lives in `litellm/config.yaml` + the `providers`/
`models` tables — the FastAPI backend never talks to provider SDKs
directly, it only reasons about the providers LiteLLM has been configured
with).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model import Model
from app.db.models.provider import Provider


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    display_name: str
    enabled: bool


def get_provider(db: Session, provider_name: str) -> ProviderInfo | None:
    row = db.execute(select(Provider).where(Provider.name == provider_name)).scalar_one_or_none()
    if row is None:
        return None
    return ProviderInfo(name=row.name, display_name=row.display_name, enabled=row.enabled)


def is_model_configured(db: Session, provider: str, model: str) -> bool:
    """True iff `provider`/`model` is a known, enabled combination.

    Used by T033 to reject requests for unconfigured provider/model pairs
    with a clear, actionable error (FR-025) instead of a silent/garbage
    telemetry record.
    """

    stmt = (
        select(Model.id)
        .join(Provider, Model.provider_id == Provider.id)
        .where(
            Provider.name == provider,
            Provider.enabled.is_(True),
            Model.model_name == model,
            Model.is_active.is_(True),
        )
    )
    return db.execute(stmt).first() is not None
