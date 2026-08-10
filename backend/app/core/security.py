"""Admin authentication: bcrypt password check + signed session cookie.

Constitution Principle II: no raw credentials are ever stored — the
operator provides `ADMIN_PASSWORD_HASH` (a bcrypt hash) via configuration.
Session state is a signed, HTTP-only cookie (itsdangerous), not a DB-backed
session table, matching research.md §4 (single-admin-cookie auth for v0.1).
"""

from __future__ import annotations

import bcrypt
from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings

_SALT = "llm-lens-admin-session"


def verify_admin_password(plain_password: str) -> bool:
    """Check a plaintext password against the configured bcrypt hash."""

    settings = get_settings()
    if not settings.admin_password_hash:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            settings.admin_password_hash.encode("utf-8"),
        )
    except ValueError:
        # Malformed hash in configuration; treat as auth failure, not a crash.
        return False


def _get_serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.secret_key, salt=_SALT)


def create_session_token(admin_email: str) -> str:
    """Create a signed session token embedding the admin identity."""

    return _get_serializer().dumps({"sub": admin_email})


def read_session_token(token: str) -> str | None:
    """Validate a session token, returning the admin email or `None`."""

    settings = get_settings()
    try:
        data = _get_serializer().loads(token, max_age=settings.session_max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    subject = data.get("sub")
    return subject if isinstance(subject, str) else None


def require_admin_session(request: Request) -> str:
    """FastAPI dependency enforcing an authenticated admin session.

    Health endpoints are exempt at the router level; every other
    `/api/v1/*` route MUST depend on this (FR-023) and return 401 when
    unauthenticated, per contracts/api.md.
    """

    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    email = read_session_token(token)
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return email
