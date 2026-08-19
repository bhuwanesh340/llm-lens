"""Project API key management (T203) — feature 003 Phase 1.

Admin-session authenticated (dashboard operator managing keys), distinct
from `resolve_trace_ingest_project` in `app.api.deps` which authenticates
the SDK's own ingest calls.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AdminSession
from app.db.session import get_db
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services.api_key_service import generate_api_key, list_api_keys, revoke_api_key
from app.services.project_service import get_project

router = APIRouter(tags=["api-keys"])

_PROJECT_NOT_FOUND = {"code": "PROJECT_NOT_FOUND", "message": "Project not found"}
_KEY_NOT_FOUND = {"code": "API_KEY_NOT_FOUND", "message": "API key not found"}


@router.get("/projects/{project_id}/keys", response_model=list[ApiKeyResponse])
async def keys_list(
    project_id: uuid.UUID, _: AdminSession, db: Session = Depends(get_db)
) -> list[ApiKeyResponse]:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_PROJECT_NOT_FOUND)
    return [ApiKeyResponse.model_validate(key) for key in list_api_keys(db, project_id)]


@router.post(
    "/projects/{project_id}/keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def keys_create(
    project_id: uuid.UUID,
    payload: ApiKeyCreate,
    _: AdminSession,
    db: Session = Depends(get_db),
) -> ApiKeyCreatedResponse:
    if get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_PROJECT_NOT_FOUND)
    created = generate_api_key(db, project_id, payload.name)
    return ApiKeyCreatedResponse(
        **ApiKeyResponse.model_validate(created.api_key).model_dump(),
        key=created.plaintext,
    )


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def keys_revoke(
    key_id: uuid.UUID, _: AdminSession, db: Session = Depends(get_db)
) -> Response:
    if not revoke_api_key(db, key_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_KEY_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
