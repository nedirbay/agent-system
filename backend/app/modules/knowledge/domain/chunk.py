"""Document chunk domain model and the chunking port (Roadmap Task 8).

A chunk is a token-bounded slice of a document's extracted text. Chunks carry
back-references (`document_id`, `chunk_index`, page) so retrieved answers can
cite their source (CH-003 / DOCUMENT_CHUNKS).
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.shared.domain.entity import BaseEntity


@dataclass
class DocumentChunk(BaseEntity):
    document_id: uuid.UUID | None = None
    chunk_index: int = 0
    content: str = ""
    token_count: int = 0
    page: int | None = None
    # Set once the chunk has been embedded and stored in the vector index.
    embedding_model: str | None = None
    embedded: bool = False


@dataclass
class ChunkDraft:
    """A chunk produced by the chunker, before it is assigned an identity."""

    chunk_index: int
    content: str
    token_count: int
    page: int | None = None


class Chunker(ABC):
    """Port: split extracted document text into token-bounded chunks (CH-001)."""

    @abstractmethod
    def split(self, text: str) -> list[ChunkDraft]:
        """Return ordered chunk drafts for the given text."""


class ChunkRepository(ABC):
    """Persistence port for DocumentChunk aggregates."""

    @abstractmethod
    async def add_many(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Persist a batch of chunks."""

    @abstractmethod
    async def delete_for_document(self, document_id: uuid.UUID) -> int:
        """Remove every chunk belonging to a document; return how many were removed."""

    @abstractmethod
    async def list_for_document(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        """Return a document's chunks in chunk_index order."""
