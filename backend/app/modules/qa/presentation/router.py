from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.qa.application.commands import CreateQaConversationCommand
from app.modules.qa.application.qa_agent import QaAgentService
from app.modules.qa.application.services import QaConversationService
from app.modules.qa.presentation.dependencies import (
    get_qa_agent_service,
    get_qaconversation_service,
)
from app.modules.qa.presentation.schemas import (
    QaAnswerRead,
    QaAskRequest,
    QaCitationRead,
    QaConversationCreate,
    QaConversationRead,
)

router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("/ask", response_model=QaAnswerRead)
async def ask_question(
    payload: QaAskRequest,
    service: QaAgentService = Depends(get_qa_agent_service),
) -> QaAnswerRead:
    """Answer a question with the RAG Q&A Agent (retrieve → grounded answer)."""
    result = await service.ask(
        payload.question, top_k=payload.top_k, document_id=payload.document_id
    )
    return QaAnswerRead(
        question=result.question,
        answer=result.answer,
        grounded=result.grounded,
        llm_used=result.llm_used,
        citations=[
            QaCitationRead(
                index=c.index,
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                chunk_index=c.chunk_index,
                page=c.page,
                score=c.score,
                snippet=c.snippet,
            )
            for c in result.citations
        ],
    )


@router.post("", response_model=QaConversationRead, status_code=201)
async def create_qaconversation(
    payload: QaConversationCreate,
    service: QaConversationService = Depends(get_qaconversation_service),
) -> QaConversationRead:
    command = CreateQaConversationCommand(**payload.model_dump())
    entity = await service.create(command)
    return QaConversationRead.model_validate(entity)


@router.get("", response_model=list[QaConversationRead])
async def list_qaconversation(
    limit: int = 100,
    offset: int = 0,
    service: QaConversationService = Depends(get_qaconversation_service),
) -> list[QaConversationRead]:
    items = await service.list(limit=limit, offset=offset)
    return [QaConversationRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=QaConversationRead)
async def get_qaconversation(
    item_id: uuid.UUID,
    service: QaConversationService = Depends(get_qaconversation_service),
) -> QaConversationRead:
    entity = await service.get(item_id)
    return QaConversationRead.model_validate(entity)
