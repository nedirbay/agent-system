"""Request authentication dependency (Faza 10 Task 30 / SEC-001, IAM).

Provides `get_current_user`: a FastAPI dependency that extracts and verifies the
Bearer JWT minted by `/auth/login`, exposing the authenticated identity to
protected endpoints. Verification is stateless (signature + expiry), so it adds
no database round-trip and scales horizontally (Task 31).

Routes opt in by depending on `get_current_user`; this is the building block for
enforcing RBAC at the gateway as endpoints are progressively locked down.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token

# auto_error=False so we raise our own JSON-enveloped 401 (not Starlette's).
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    username: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("Token is missing a subject")
    return CurrentUser(id=str(subject), username=payload.get("username"))
