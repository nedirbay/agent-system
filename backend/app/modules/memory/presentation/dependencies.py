from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import get_redis
from app.core.database import get_session
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository
from app.modules.knowledge.application.indexing import KnowledgeIndexService
from app.modules.knowledge.infrastructure.chunk_repository import SqlAlchemyChunkRepository
from app.modules.knowledge.infrastructure.chunker import StructureAwareChunker
from app.modules.knowledge.infrastructure.embedding import HashingEmbeddingProvider
from app.modules.knowledge.infrastructure.source import RepositoryDocumentSource
from app.modules.knowledge.infrastructure.vector_store import QdrantVectorStore
from app.modules.memory.application.long_term_memory import LongTermMemoryService
from app.modules.memory.application.memory_agent import MemoryAgentService
from app.modules.memory.application.services import MemoryItemService
from app.modules.memory.application.session_memory import SessionMemoryService
from app.modules.memory.infrastructure.memory_vector import QdrantMemoryVectorIndex
from app.modules.memory.infrastructure.repositories import (
    SqlAlchemyMemoryItemRepository,
    SqlAlchemyMemoryReferenceRepository,
)
from app.modules.memory.infrastructure.session_store import RedisSessionMemoryStore


def get_memoryitem_service(session: AsyncSession = Depends(get_session)) -> MemoryItemService:
    return MemoryItemService(SqlAlchemyMemoryItemRepository(session))


def get_session_memory_service() -> SessionMemoryService:
    return SessionMemoryService(RedisSessionMemoryStore(get_redis()))


def get_long_term_memory_service(
    session: AsyncSession = Depends(get_session),
) -> LongTermMemoryService:
    return LongTermMemoryService(
        items=SqlAlchemyMemoryItemRepository(session),
        references=SqlAlchemyMemoryReferenceRepository(session),
        embedder=HashingEmbeddingProvider(),
        vectors=QdrantMemoryVectorIndex(),
    )


def get_memory_agent_service(
    session: AsyncSession = Depends(get_session),
) -> MemoryAgentService:
    knowledge = KnowledgeIndexService(
        source=RepositoryDocumentSource(SqlAlchemyDocumentRepository(session)),
        chunker=StructureAwareChunker(),
        chunks=SqlAlchemyChunkRepository(session),
        embedder=HashingEmbeddingProvider(),
        vector_store=QdrantVectorStore(),
    )
    return MemoryAgentService(
        session=get_session_memory_service(),
        long_term=get_long_term_memory_service(session),
        knowledge=knowledge,
    )
