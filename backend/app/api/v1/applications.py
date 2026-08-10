"""`/api/v1/applications` CRUD endpoints (T057, US4)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AdminSession
from app.db.session import get_db
from app.schemas.applications import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from app.services.application_service import (
    DuplicateSlugError,
    create_application,
    delete_application,
    get_application,
    list_applications,
    update_application,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
async def applications_list(
    _: AdminSession, db: Session = Depends(get_db)
) -> list[ApplicationResponse]:
    return [ApplicationResponse.model_validate(app) for app in list_applications(db)]


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def applications_create(
    payload: ApplicationCreate, _: AdminSession, db: Session = Depends(get_db)
) -> ApplicationResponse:
    try:
        app = create_application(db, payload)
    except DuplicateSlugError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_SLUG", "message": str(exc)},
        ) from exc
    return ApplicationResponse.model_validate(app)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def applications_detail(
    application_id: uuid.UUID, _: AdminSession, db: Session = Depends(get_db)
) -> ApplicationResponse:
    app = get_application(db, application_id)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )
    return ApplicationResponse.model_validate(app)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def applications_update(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    _: AdminSession,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    app = update_application(db, application_id, payload)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )
    return ApplicationResponse.model_validate(app)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def applications_delete(
    application_id: uuid.UUID, _: AdminSession, db: Session = Depends(get_db)
) -> Response:
    deleted = delete_application(db, application_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
