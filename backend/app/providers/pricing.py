"""Pricing registry (T025): `get_model_pricing(provider, model)`.

Backed by the `models` table (data-model.md). Returns `None` when pricing is
unknown so callers (cost_service.py) can distinguish "unknown" from
"explicitly zero" per constitution Principle III / FR-006 / FR-007.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.model import Model
from app.db.models.provider import Provider


@dataclass(frozen=True)
class ModelPricing:
    """Per-1M-token pricing for a single provider/model pair.

    Both fields are `None` when pricing is unknown (never coerced to 0);
    a model explicitly configured as zero-cost stores `Decimal("0")`.
    """

    input_price_per_1m: Decimal | None
    output_price_per_1m: Decimal | None
    currency: str = "USD"


def get_model_pricing(db: Session, provider: str, model: str) -> ModelPricing | None:
    """Look up pricing for a provider/model pair.

    Returns `None` if the provider/model is not registered at all (pricing
    truly unknown, distinct from a registered model with `NULL` price
    columns — both ultimately yield a `NULL` cost, but this distinction
    matters for T033's unconfigured-model error handling).
    """

    stmt = (
        select(Model)
        .join(Provider, Model.provider_id == Provider.id)
        .where(Provider.name == provider, Model.model_name == model)
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        return None
    return ModelPricing(
        input_price_per_1m=row.input_price_per_1m,
        output_price_per_1m=row.output_price_per_1m,
        currency=row.currency,
    )
