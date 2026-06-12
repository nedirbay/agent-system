from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.knowledge.application.commands import (
    CreateKnowledgeItemCommand,
    SearchQuery,
)
from app.modules.knowledge.application.indexing import KnowledgeIndexService
from app.modules.knowledge.application.services import KnowledgeItemService
from app.modules.knowledge.presentation.dependencies import (
    get_knowledge_index_service,
    get_knowledgeitem_service,
)
from app.modules.knowledge.presentation.schemas import (
    IndexResultRead,
    KnowledgeItemCreate,
    KnowledgeItemRead,
    SearchRequest,
    SearchResponse,
    SearchResultRead,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post("/documents/{document_id}/index", response_model=IndexResultRead)
async def index_document(
    document_id: uuid.UUID,
    service: KnowledgeIndexService = Depends(get_knowledge_index_service),
) -> IndexResultRead:
    """Chunk a parsed document, embed the chunks, and store them in Qdrant.

    Re-running re-indexes: prior chunks/vectors for the document are replaced.
    """
    result = await service.index_document(document_id)
    return IndexResultRead(
        document_id=result.document_id,
        chunk_count=result.chunk_count,
        embedded_count=result.embedded_count,
        embedding_model=result.embedding_model,
        collection=result.collection,
    )


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    payload: SearchRequest,
    service: KnowledgeIndexService = Depends(get_knowledge_index_service),
) -> SearchResponse:
    """Semantic search over indexed document chunks (vector similarity)."""
    hits = await service.search(
        SearchQuery(
            query=payload.query,
            top_k=payload.top_k,
            document_id=payload.document_id,
        )
    )
    return SearchResponse(
        query=payload.query,
        count=len(hits),
        results=[
            SearchResultRead(
                chunk_id=h.chunk_id,
                document_id=h.document_id,
                chunk_index=h.chunk_index,
                score=h.score,
                page=h.page,
                content=h.content,
            )
            for h in hits
        ],
    )


@router.post("", response_model=KnowledgeItemRead, status_code=201)
async def create_knowledgeitem(
    payload: KnowledgeItemCreate,
    service: KnowledgeItemService = Depends(get_knowledgeitem_service),
) -> KnowledgeItemRead:
    command = CreateKnowledgeItemCommand(**payload.model_dump())
    entity = await service.create(command)
    return KnowledgeItemRead.model_validate(entity)


@router.get("", response_model=list[KnowledgeItemRead])
async def list_knowledgeitem(
    limit: int = 100,
    offset: int = 0,
    service: KnowledgeItemService = Depends(get_knowledgeitem_service),
) -> list[KnowledgeItemRead]:
    items = await service.list(limit=limit, offset=offset)
    return [KnowledgeItemRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=KnowledgeItemRead)
async def get_knowledgeitem(
    item_id: uuid.UUID,
    service: KnowledgeItemService = Depends(get_knowledgeitem_service),
) -> KnowledgeItemRead:
    entity = await service.get(item_id)
    return KnowledgeItemRead.model_validate(entity)
