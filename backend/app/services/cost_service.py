"""Cost service (T030) — constitution Principle III: single, centralized,
Decimal-based cost calculation. Unknown pricing yields `NULL` (never `0`);
zero-cost is only used for models explicitly configured with a `0` price.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.providers.pricing import get_model_pricing

_PER_TOKEN_DIVISOR = Decimal(1_000_000)
_QUANTIZE = Decimal("0.00000001")  # matches NUMERIC(18,8)


@dataclass(frozen=True)
class RequestCost:
    """Result of a cost calculation for a single request.

    `input_cost`/`output_cost`/`total_cost` are `None` when pricing for the
    provider/model is unknown. `total_cost` is `None` iff either component
    is `None` (data-model.md validation rule).
    """

    input_cost: Decimal | None
    output_cost: Decimal | None
    total_cost: Decimal | None


def _price_component(tokens: int, price_per_1m: Decimal | None) -> Decimal | None:
    if price_per_1m is None:
        return None
    cost = (Decimal(tokens) * price_per_1m) / _PER_TOKEN_DIVISOR
    return cost.quantize(_QUANTIZE, rounding=ROUND_HALF_UP)


def calculate_cost(
    db: Session, provider: str, model: str, input_tokens: int, output_tokens: int
) -> RequestCost:
    """Calculate input/output/total cost for a request.

    Returns all-`None` when the provider/model pair has no pricing entry at
    all or has `NULL` price columns (pricing unknown, FR-006). Returns
    `Decimal("0")` components when the model is explicitly configured with
    a zero price (FR-007).
    """

    pricing = get_model_pricing(db, provider, model)
    if pricing is None:
        return RequestCost(input_cost=None, output_cost=None, total_cost=None)

    input_cost = _price_component(input_tokens, pricing.input_price_per_1m)
    output_cost = _price_component(output_tokens, pricing.output_price_per_1m)

    if input_cost is None or output_cost is None:
        return RequestCost(input_cost=input_cost, output_cost=output_cost, total_cost=None)

    return RequestCost(
        input_cost=input_cost, output_cost=output_cost, total_cost=input_cost + output_cost
    )
