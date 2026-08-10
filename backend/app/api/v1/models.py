"""`GET /api/v1/models`, `/models/{model_id}` (T044, US2).

`model_id` is the model name string as recorded on `llm_requests.model`
(the identifier requests/usage/costs already key on) rather than the
`models` pricing-config table's surrogate UUID, since analytics are
computed over recorded requests, not the pricing catalog.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import AdminSession, RangeFilterDep
from app.db.session import get_db
from app.schemas.analytics import ModelDetailResponse, ModelSummaryItem
from app.services.analytics_service import get_model_summaries, get_model_summary

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelSummaryItem])
async def models(
    _: AdminSession, filters: RangeFilterDep, db: Session = Depends(get_db)
) -> list[ModelSummaryItem]:
    return [ModelSummaryItem.model_validate(row) for row in get_model_summaries(db, filters)]


@router.get("/{model_id}", response_model=ModelDetailResponse)
async def model_detail(
    model_id: str,
    _: AdminSession,
    filters: RangeFilterDep,
    db: Session = Depends(get_db),
) -> ModelDetailResponse:
    result = get_model_summary(db, filters, model_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "MODEL_NOT_FOUND",
                "message": f"No requests found for model '{model_id}'",
            },
        )
    return ModelDetailResponse.model_validate(result)
