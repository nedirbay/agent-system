from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response

from app.modules.memory.application.commands import CreateMemoryItemCommand
from app.modules.memory.application.long_term_memory import (
    LongTermMemoryService,
    MemoryRef,
)
from app.modules.memory.application.memory_agent import MemoryAgentService
from app.modules.memory.application.services import MemoryItemService
from app.modules.memory.application.session_memory import SessionMemoryService
from app.modules.memory.presentation.dependencies import (
    get_long_term_memory_service,
    get_memory_agent_service,
    get_memoryitem_service,
    get_session_memory_service,
)
from app.modules.memory.presentation.schemas import (
    AppendTurnRequest,
    AssembleContextRequest,
    KnowledgeMemoryRead,
    MemoryContextRead,
    MemoryItemCreate,
    MemoryItemRead,
    MemoryReferenceRead,
    RecallRequest,
    RecalledMemoryRead,
    RememberRequest,
    SessionContextRead,
    SessionTurnRead,
)

router = APIRouter(prefix="/memory", tags=["Memory"])


# --- Session memory (Task 18) ---


def _session_context_read(ctx) -> SessionContextRead:
    return SessionContextRead(
        session_id=ctx.session_id,
        summary=ctx.summary,
        turns=[
            SessionTurnRead(role=t.role, content=t.content, created_at=t.created_at)
            for t in ctx.turns
        ],
        text=ctx.text,
    )


@router.post("/sessions/{session_id}/turns", response_model=SessionContextRead)
async def append_session_turn(
    session_id: str,
    payload: AppendTurnRequest,
    service: SessionMemoryService = Depends(get_session_memory_service),
) -> SessionContextRead:
    ctx = await service.append_turn(session_id, payload.role, payload.content)
    return _session_context_read(ctx)


@router.get("/sessions/{session_id}", response_model=SessionContextRead)
async def get_session_context(
    session_id: str,
    service: SessionMemoryService = Depends(get_session_memory_service),
) -> SessionContextRead:
    ctx = await service.get_context(session_id)
    return _session_context_read(ctx)


@router.delete("/sessions/{session_id}", status_code=204, response_class=Response)
async def clear_session(
    session_id: str,
    service: SessionMemoryService = Depends(get_session_memory_service),
) -> Response:
    await service.clear(session_id)
    return Response(status_code=204)


# --- Long-term memory (Task 19) ---


def _recalled_read(m) -> RecalledMemoryRead:
    return RecalledMemoryRead(
        memory_id=m.memory_id,
        memory_type=m.memory_type,
        content=m.content,
        importance_score=m.importance_score,
        score=m.score,
        references=[
            MemoryReferenceRead(
                related_entity_type=r.related_entity_type,
                related_entity_id=r.related_entity_id,
            )
            for r in m.references
        ],
    )


@router.post("/long-term", response_model=MemoryItemRead, status_code=201)
async def remember(
    payload: RememberRequest,
    service: LongTermMemoryService = Depends(get_long_term_memory_service),
) -> MemoryItemRead:
    item = await service.remember(
        payload.content,
        memory_type=payload.memory_type,
        importance_score=payload.importance_score,
        references=[
            MemoryRef(
                related_entity_type=r.related_entity_type,
                related_entity_id=r.related_entity_id,
            )
            for r in payload.references
        ],
    )
    return MemoryItemRead.model_validate(item)


@router.post("/long-term/recall", response_model=list[RecalledMemoryRead])
async def recall(
    payload: RecallRequest,
    service: LongTermMemoryService = Depends(get_long_term_memory_service),
) -> list[RecalledMemoryRead]:
    results = await service.recall(
        payload.query, top_k=payload.top_k, memory_type=payload.memory_type
    )
    return [_recalled_read(m) for m in results]


# --- Memory Agent context assembly (Task 20) ---


@router.post("/context", response_model=MemoryContextRead)
async def assemble_context(
    payload: AssembleContextRequest,
    service: MemoryAgentService = Depends(get_memory_agent_service),
) -> MemoryContextRead:
    ctx = await service.assemble_context(
        payload.query,
        session_id=payload.session_id,
        working=payload.working,
        top_k=payload.top_k,
        memory_type=payload.memory_type,
        document_id=payload.document_id,
    )
    return MemoryContextRead(
        query=ctx.query,
        session_id=ctx.session_id,
        working=ctx.working,
        session=ctx.session,
        long_term=[_recalled_read(m) for m in ctx.long_term],
        knowledge=[
            KnowledgeMemoryRead(
                chunk_id=k.chunk_id,
                document_id=k.document_id,
                score=k.score,
                snippet=k.snippet,
            )
            for k in ctx.knowledge
        ],
        text=ctx.text,
    )


# --- CRUD (scaffold) ---


@router.post("", response_model=MemoryItemRead, status_code=201)
async def create_memoryitem(
    payload: MemoryItemCreate,
    service: MemoryItemService = Depends(get_memoryitem_service),
) -> MemoryItemRead:
    command = CreateMemoryItemCommand(**payload.model_dump())
    entity = await service.create(command)
    return MemoryItemRead.model_validate(entity)


@router.get("", response_model=list[MemoryItemRead])
async def list_memoryitem(
    limit: int = 100,
    offset: int = 0,
    service: MemoryItemService = Depends(get_memoryitem_service),
) -> list[MemoryItemRead]:
    items = await service.list(limit=limit, offset=offset)
    return [MemoryItemRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=MemoryItemRead)
async def get_memoryitem(
    item_id: uuid.UUID,
    service: MemoryItemService = Depends(get_memoryitem_service),
) -> MemoryItemRead:
    entity = await service.get(item_id)
    return MemoryItemRead.model_validate(entity)
