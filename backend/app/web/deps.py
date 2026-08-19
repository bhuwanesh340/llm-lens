"""Page-level (browser) auth for the Jinja UI — distinct from the JSON-401
`require_admin_session` used by `/api/v1/*`. An unauthenticated page request
redirects to `/login` instead of returning a JSON error body. The redirect
itself is handled by `redirect_to_login_exception_handler` in `app.main`.
"""

from __future__ import annotations

from fastapi import Request

from app.core.config import get_settings
from app.core.security import read_session_token


class RedirectToLogin(Exception):
    def __init__(self, next_path: str) -> None:
        super().__init__("Not authenticated")
        self.next_path = next_path


def require_admin_page_session(request: Request) -> str:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    email = read_session_token(token) if token else None
    if email is None:
        raise RedirectToLogin(next_path=str(request.url.path))
    return email
