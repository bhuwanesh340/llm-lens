"""Unit tests for the cost service (T022).

Covers: known price, unknown price -> NULL, zero-cost provider -> 0
(constitution Principle III / FR-006 / FR-007).
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.model import Model
from app.db.models.provider import Provider
from app.services.cost_service import calculate_cost


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


def test_known_price_calculates_expected_cost(pricing_db_session: Session) -> None:
    _add_provider_and_model(
        pricing_db_session, "openai", "gpt-4o-mini", Decimal("0.15"), Decimal("0.60")
    )

    cost = calculate_cost(
        pricing_db_session, "openai", "gpt-4o-mini", input_tokens=1_000_000, output_tokens=500_000
    )

    assert cost.input_cost == Decimal("0.15000000")
    assert cost.output_cost == Decimal("0.30000000")
    assert cost.total_cost == Decimal("0.45000000")


def test_unknown_pricing_yields_null_never_zero(pricing_db_session: Session) -> None:
    cost = calculate_cost(
        pricing_db_session, "openai", "unregistered-model", input_tokens=100, output_tokens=50
    )

    assert cost.input_cost is None
    assert cost.output_cost is None
    assert cost.total_cost is None


def test_zero_cost_provider_yields_zero(pricing_db_session: Session) -> None:
    _add_provider_and_model(pricing_db_session, "ollama", "llama3", Decimal("0"), Decimal("0"))

    cost = calculate_cost(
        pricing_db_session, "ollama", "llama3", input_tokens=1000, output_tokens=1000
    )

    assert cost.input_cost == Decimal("0.00000000")
    assert cost.output_cost == Decimal("0.00000000")
    assert cost.total_cost == Decimal("0.00000000")
