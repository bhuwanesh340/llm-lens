"""Admin session authentication endpoints.

Not an explicit numbered task in tasks.md, but required infrastructure for
FR-023 / contracts/api.md's "Authentication" section: sessions are
established via a login endpoint that verifies the operator-configured
admin credentials and issues a signed, HTTP-only session cookie (research.md
§4). Exempt from `require_admin_session` (chicken-and-egg), except `/me`
which reports current auth state for the frontend shell.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings
from app.core.security import create_session_token, read_session_token, verify_admin_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionResponse(BaseModel):
    authenticated: bool
    email: str | None = None


def _read_optional_session(request: Request) -> str | None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    return read_session_token(token)


@router.post("/login", response_model=SessionResponse)
async def login(payload: LoginRequest, response: Response) -> SessionResponse:
    settings = get_settings()
    if payload.email.lower() != settings.admin_email.lower() or not verify_admin_password(
        payload.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    token = create_session_token(settings.admin_email)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
    )
    return SessionResponse(authenticated=True, email=settings.admin_email)


@router.post("/logout", response_model=SessionResponse)
async def logout(response: Response) -> SessionResponse:
    settings = get_settings()
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return SessionResponse(authenticated=False)


@router.get("/session", response_model=SessionResponse)
async def session_status(request: Request) -> SessionResponse:
    email = _read_optional_session(request)
    return SessionResponse(authenticated=email is not None, email=email)
