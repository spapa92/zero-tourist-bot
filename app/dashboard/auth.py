"""Middleware Basic Auth per la dashboard: protegge tutto tranne webhook e health."""

from __future__ import annotations

import base64
import secrets

from starlette.requests import Request
from starlette.responses import Response

PUBLIC_PATHS = {"/webhook", "/health"}


def _unauthorized() -> Response:
    return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="dashboard"'})


def _credentials_match(header_value: str, username: str, password: str) -> bool:
    if not username or not password:
        # Fail-closed: senza credenziali configurate la dashboard resta bloccata.
        return False
    if not header_value.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header_value.removeprefix("Basic ")).decode("utf-8")
        given_user, given_password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return False
    return secrets.compare_digest(given_user, username) and secrets.compare_digest(
        given_password, password
    )


async def basic_auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    settings = request.app.state.settings
    header_value = request.headers.get("Authorization", "")
    if not _credentials_match(header_value, settings.dashboard_username, settings.dashboard_password):
        return _unauthorized()

    return await call_next(request)
