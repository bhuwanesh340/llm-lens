"""Unit tests for the pricing registry (T022)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.model import Model
from app.db.models.provider import Provider
from app.providers.pricing import get_model_pricing


def _add_provider_and_model(
    db: Session,
    provider_name: str,
    model_name: str,
    input_price: Decimal | None,
    output_price: Decimal | None,
) -> None:
    provider = Provider(name=provider_name, display_name=provider_name.title(), enabled=True)
    db.add(provider)
    db.flush()
    model = Model(
        provider_id=provider.id,
        model_name=model_name,
        display_name=model_name,
        input_price_per_1m=input_price,
        output_price_per_1m=output_price,
        currency="USD",
        is_active=True,
    )
    db.add(model)
    db.commit()


def test_known_pricing_returns_prices(pricing_db_session: Session) -> None:
    _add_provider_and_model(
        pricing_db_session, "openai", "gpt-4o-mini", Decimal("0.15"), Decimal("0.60")
    )

    pricing = get_model_pricing(pricing_db_session, "openai", "gpt-4o-mini")

    assert pricing is not None
    assert pricing.input_price_per_1m == Decimal("0.15")
    assert pricing.output_price_per_1m == Decimal("0.60")


def test_unregistered_model_returns_none(pricing_db_session: Session) -> None:
    pricing = get_model_pricing(pricing_db_session, "openai", "does-not-exist")

    assert pricing is None


def test_zero_cost_model_returns_zero_not_none(pricing_db_session: Session) -> None:
    _add_provider_and_model(
        pricing_db_session, "ollama", "llama3", Decimal("0"), Decimal("0")
    )

    pricing = get_model_pricing(pricing_db_session, "ollama", "llama3")

    assert pricing is not None
    assert pricing.input_price_per_1m == Decimal("0")
    assert pricing.output_price_per_1m == Decimal("0")


def test_registered_model_with_null_price_is_unknown(pricing_db_session: Session) -> None:
    _add_provider_and_model(pricing_db_session, "custom", "new-model", None, None)

    pricing = get_model_pricing(pricing_db_session, "custom", "new-model")

    assert pricing is not None
    assert pricing.input_price_per_1m is None
    assert pricing.output_price_per_1m is None
