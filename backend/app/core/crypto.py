"""Symmetric encryption for secrets at rest (connector tokens, API keys).

Third-party credentials (Slack bot tokens, Gmail app passwords, WhatsApp access
tokens, …) must never be stored in plaintext. Every secret is sealed with
Fernet (AES-128-CBC + HMAC-SHA256 authenticated encryption) before it touches
the database, and decrypted only at the moment an agent needs to use it.

The encryption key is derived from ``connector_encryption_key`` (a dedicated
secret, separate from the JWT signing key). In production it MUST be set from a
secret manager and rotated independently; if left empty we fall back to the JWT
secret so local dev still works, but that is not a production posture.
"""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class SecretDecryptionError(Exception):
    """Raised when a stored ciphertext cannot be decrypted (wrong/rotated key)."""


def _derive_key(secret: str) -> bytes:
    """Map an arbitrary passphrase to a 32-byte urlsafe-base64 Fernet key."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache
def _fernet() -> Fernet:
    settings = get_settings()
    secret = settings.connector_encryption_key or settings.jwt_secret
    return Fernet(_derive_key(secret))


def encrypt_secret(plaintext: str) -> str:
    """Seal a secret; returns an opaque urlsafe-base64 token safe to persist."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str:
    """Open a previously sealed secret. Raises on tampering or key mismatch."""
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:  # pragma: no cover - defensive
        raise SecretDecryptionError("Could not decrypt stored secret") from exc


def mask_secret(plaintext: str) -> str:
    """A display-safe hint that reveals only the last few characters."""
    tail = plaintext[-4:] if len(plaintext) >= 4 else ""
    return f"••••{tail}" if tail else "••••"
