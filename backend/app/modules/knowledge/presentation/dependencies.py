from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository
from app.modules.knowledge.application.indexing import KnowledgeIndexService
from app.modules.knowledge.application.services import KnowledgeItemService
from app.modules.knowledge.infrastructure.chunk_repository import SqlAlchemyChunkRepository
from app.modules.knowledge.infrastructure.chunker import StructureAwareChunker
from app.modules.knowledge.infrastructure.embedding import HashingEmbeddingProvider
from app.modules.knowledge.infrastructure.repositories import SqlAlchemyKnowledgeItemRepository
from app.modules.knowledge.infrastructure.source import RepositoryDocumentSource
from app.modules.knowledge.infrastructure.vector_store import QdrantVectorStore


def get_knowledgeitem_service(session: AsyncSession = Depends(get_session)) -> KnowledgeItemService:
    return KnowledgeItemService(SqlAlchemyKnowledgeItemRepository(session))


def get_knowledge_index_service(
    session: AsyncSession = Depends(get_session),
) -> KnowledgeIndexService:
    return KnowledgeIndexService(
        source=RepositoryDocumentSource(SqlAlchemyDocumentRepository(session)),
        chunker=StructureAwareChunker(),
        chunks=SqlAlchemyChunkRepository(session),
        embedder=HashingEmbeddingProvider(),
        vector_store=QdrantVectorStore(),
    )
