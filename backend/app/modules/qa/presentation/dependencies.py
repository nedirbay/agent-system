from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository
from app.modules.knowledge.application.indexing import KnowledgeIndexService
from app.modules.knowledge.infrastructure.chunk_repository import SqlAlchemyChunkRepository
from app.modules.knowledge.infrastructure.chunker import StructureAwareChunker
from app.modules.knowledge.infrastructure.embedding import HashingEmbeddingProvider
from app.modules.knowledge.infrastructure.source import RepositoryDocumentSource
from app.modules.knowledge.infrastructure.vector_store import QdrantVectorStore
from app.modules.qa.application.qa_agent import QaAgentService
from app.modules.qa.application.services import QaConversationService
from app.modules.qa.infrastructure.repositories import SqlAlchemyQaConversationRepository
from app.shared.llm import get_llm_provider


def get_qaconversation_service(session: AsyncSession = Depends(get_session)) -> QaConversationService:
    return QaConversationService(SqlAlchemyQaConversationRepository(session))


def get_qa_agent_service(session: AsyncSession = Depends(get_session)) -> QaAgentService:
    retriever = KnowledgeIndexService(
        source=RepositoryDocumentSource(SqlAlchemyDocumentRepository(session)),
        chunker=StructureAwareChunker(),
        chunks=SqlAlchemyChunkRepository(session),
        embedder=HashingEmbeddingProvider(),
        vector_store=QdrantVectorStore(),
    )
    return QaAgentService(retriever=retriever, llm=get_llm_provider())
