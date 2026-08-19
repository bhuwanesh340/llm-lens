"""Login/logout pages for the Jinja UI (pulled forward from feature 002/003
Phase 4 T239 — needed now so the trace UI is reachable without the React
app or manual cookie forging)."""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.security import create_session_token, verify_admin_password
from app.web.templating import templates

router = APIRouter(tags=["web"])
_DEFAULT_NEXT = "/traces"


@router.get("/login")
async def login_page(request: Request, next: str = _DEFAULT_NEXT) -> object:
    return templates.TemplateResponse(request, "login.html", {"error": None, "next": next})


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(_DEFAULT_NEXT),
) -> object:
    settings = get_settings()
    if email.lower() != settings.admin_email.lower() or not verify_admin_password(password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid email or password", "next": next},
            status_code=401,
        )

    token = create_session_token(settings.admin_email)
    response = RedirectResponse(url=next or _DEFAULT_NEXT, status_code=303)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    settings = get_settings()
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response
