"""Projects & API keys admin page (T237) — Jinja port of frontend/src/app/projects/*."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.projects import ProjectCreate
from app.services.api_key_service import generate_api_key, list_api_keys, revoke_api_key
from app.services.project_service import (
    DuplicateSlugError,
    InvalidProjectNameError,
    create_project,
    delete_project,
    get_project,
    list_projects,
)
from app.web.deps import require_admin_page_session
from app.web.templating import templates

router = APIRouter(tags=["web"], dependencies=[Depends(require_admin_page_session)])


@router.get("/projects")
async def projects_page(request: Request, db: Session = Depends(get_db)) -> object:
    projects = list_projects(db)
    context = {"projects": projects, "error": None, "created_key": None}
    return templates.TemplateResponse(request, "projects/page.html", context)


@router.post("/projects")
async def create_project_submit(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    environment: str = Form(""),
    db: Session = Depends(get_db),
) -> object:
    error = None
    try:
        create_project(
            db,
            ProjectCreate(
                name=name,
                description=description or None,
                environment=environment or None,
            ),
        )
    except (DuplicateSlugError, InvalidProjectNameError) as exc:
        error = str(exc)

    projects = list_projects(db)
    context = {"projects": projects, "error": error, "created_key": None}
    return templates.TemplateResponse(request, "projects/page.html", context)


@router.post("/projects/{project_id}/delete")
async def delete_project_submit(
    request: Request, project_id: uuid.UUID, db: Session = Depends(get_db)
) -> object:
    delete_project(db, project_id)
    return RedirectResponse(url="/projects", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/projects/{project_id}")
async def project_detail_page(
    request: Request, project_id: uuid.UUID, db: Session = Depends(get_db)
) -> object:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    keys = list_api_keys(db, project_id)
    context = {"project": project, "keys": keys, "created_key": None}
    return templates.TemplateResponse(request, "projects/detail.html", context)


@router.post("/projects/{project_id}/keys")
async def create_api_key_submit(
    request: Request, project_id: uuid.UUID, name: str = Form(...), db: Session = Depends(get_db)
) -> object:
    project = get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    created = generate_api_key(db, project_id, name)
    keys = list_api_keys(db, project_id)
    context = {"project": project, "keys": keys, "created_key": created.plaintext}
    return templates.TemplateResponse(request, "projects/detail.html", context)


@router.post("/projects/{project_id}/keys/{key_id}/revoke")
async def revoke_api_key_submit(
    request: Request, project_id: uuid.UUID, key_id: uuid.UUID, db: Session = Depends(get_db)
) -> object:
    revoke_api_key(db, key_id)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=status.HTTP_303_SEE_OTHER)
