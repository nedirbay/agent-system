from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StoredObject:
    """Result of persisting a file in object storage."""

    key: str
    size: int
    content_type: str | None = None


class FileStorage(ABC):
    """Port for binary object storage (S3 / MinIO).

    Kept in the domain layer so the application service depends on this
    abstraction, not on the MinIO SDK. Implemented in `infrastructure/`.
    """

    @abstractmethod
    async def ensure_ready(self) -> None:
        """Make sure the backing bucket exists (idempotent)."""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str | None) -> StoredObject:
        """Store `data` under `key` and return its metadata."""

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Read the object's full contents back into memory."""

    @abstractmethod
    async def presigned_get_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Return a time-limited URL the client can use to download the object directly."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove the object (no error if it is already gone)."""
