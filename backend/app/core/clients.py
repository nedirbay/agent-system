"""Lazy singletons for cross-cutting infrastructure clients.

Each client is created on first use and does not connect at import time, so the
API boots without Redis / Qdrant / MinIO / an LLM endpoint being available.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:  # pragma: no cover
    from minio import Minio
    from qdrant_client import QdrantClient
    from redis.asyncio import Redis


@lru_cache
def get_redis() -> "Redis":
    from redis.asyncio import Redis

    return Redis.from_url(get_settings().redis_url, decode_responses=True)


@lru_cache
def get_qdrant() -> "QdrantClient":
    from qdrant_client import QdrantClient

    return QdrantClient(url=get_settings().qdrant_url)


@lru_cache
def get_object_storage() -> "Minio":
    from minio import Minio

    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
