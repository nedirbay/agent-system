from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateKnowledgeItemCommand:
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    title: str | None = None
    content: str | None = None


@dataclass
class IndexResult:
    """Outcome of indexing one document into the knowledge layer."""

    document_id: uuid.UUID
    chunk_count: int
    embedded_count: int
    embedding_model: str
    collection: str


@dataclass
class SearchQuery:
    query: str
    top_k: int = 5
    document_id: uuid.UUID | None = None


@dataclass
class SearchResultItem:
    chunk_id: uuid.UUID
    document_id: uuid.UUID | None
    chunk_index: int | None
    score: float
    page: int | None
    content: str

