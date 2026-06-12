"""Password hashing and JWT helpers (FR-001, SEC-001)."""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

# bcrypt operates on at most 72 bytes; longer secrets are truncated by the algorithm.
_MAX_BCRYPT_BYTES = 72


def hash_password(plain: str) -> str:
    digest = bcrypt.hashpw(plain.encode()[:_MAX_BCRYPT_BYTES], bcrypt.gensalt())
    return digest.decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode()[:_MAX_BCRYPT_BYTES], hashed.encode())
    except ValueError:
        return False


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire, **(extra or {})}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - thin wrapper
        raise UnauthorizedError("Invalid or expired token") from exc
