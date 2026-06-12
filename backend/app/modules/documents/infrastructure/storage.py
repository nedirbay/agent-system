from __future__ import annotations

import io
from datetime import timedelta

from starlette.concurrency import run_in_threadpool

from app.core.clients import get_object_storage
from app.core.config import get_settings
from app.modules.documents.domain.storage import FileStorage, StoredObject


class MinioFileStorage(FileStorage):
    """MinIO/S3 adapter for the FileStorage port.

    The MinIO SDK is synchronous, so every call is offloaded to a worker
    thread to avoid blocking the event loop.
    """

    def __init__(self) -> None:
        self._client = get_object_storage()  # lazy: does not connect here
        self._bucket = get_settings().documents_bucket

    async def ensure_ready(self) -> None:
        await run_in_threadpool(self._ensure_bucket_sync)

    def _ensure_bucket_sync(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    async def upload(self, key: str, data: bytes, content_type: str | None) -> StoredObject:
        await run_in_threadpool(self._put_sync, key, data, content_type)
        return StoredObject(key=key, size=len(data), content_type=content_type)

    def _put_sync(self, key: str, data: bytes, content_type: str | None) -> None:
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type or "application/octet-stream",
        )

    async def download(self, key: str) -> bytes:
        return await run_in_threadpool(self._get_sync, key)

    def _get_sync(self, key: str) -> bytes:
        response = self._client.get_object(self._bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def presigned_get_url(self, key: str, expires_seconds: int = 3600) -> str:
        return await run_in_threadpool(
            self._client.presigned_get_object,
            self._bucket,
            key,
            timedelta(seconds=expires_seconds),
        )

    async def delete(self, key: str) -> None:
        await run_in_threadpool(self._client.remove_object, self._bucket, key)
