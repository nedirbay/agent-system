from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeItemCreate(BaseModel):
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    title: str | None = None
    content: str | None = None


class KnowledgeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    title: str | None = None
    content: str | None = None


class IndexResultRead(BaseModel):
    """Outcome of indexing a document (chunk → embed → store)."""

    document_id: uuid.UUID
    chunk_count: int
    embedded_count: int
    embedding_model: str
    collection: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    document_id: uuid.UUID | None = None


class SearchResultRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID | None = None
    chunk_index: int | None = None
    score: float
    page: int | None = None
    content: str


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResultRead]
