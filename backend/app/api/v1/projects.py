"""`/api/v1/projects` CRUD endpoints (T110)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AdminSession
from app.db.session import get_db
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import (
    DuplicateSlugError,
    InvalidProjectNameError,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])

_NOT_FOUND = {"code": "PROJECT_NOT_FOUND", "message": "Project not found"}


@router.get("", response_model=list[ProjectResponse])
async def projects_list(_: AdminSession, db: Session = Depends(get_db)) -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(project) for project in list_projects(db)]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def projects_create(
    payload: ProjectCreate, _: AdminSession, db: Session = Depends(get_db)
) -> ProjectResponse:
    try:
        project = create_project(db, payload)
    except InvalidProjectNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_PROJECT_NAME", "message": str(exc)},
        ) from exc
    except DuplicateSlugError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_SLUG", "message": str(exc)},
        ) from exc
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def projects_detail(
    project_id: uuid.UUID, _: AdminSession, db: Session = Depends(get_db)
) -> ProjectResponse:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def projects_update(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    _: AdminSession,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    try:
        project = update_project(db, project_id, payload)
    except InvalidProjectNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_PROJECT_NAME", "message": str(exc)},
        ) from exc
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def projects_delete(
    project_id: uuid.UUID, _: AdminSession, db: Session = Depends(get_db)
) -> Response:
    if not delete_project(db, project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
