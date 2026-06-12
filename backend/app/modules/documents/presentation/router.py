from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.documents.application.commands import CreateDocumentCommand
from app.modules.documents.application.services import DocumentService
from app.modules.documents.presentation.dependencies import get_document_service
from app.modules.documents.presentation.schemas import DocumentCreate, DocumentRead

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentRead, status_code=201)
async def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    command = CreateDocumentCommand(**payload.model_dump())
    entity = await service.create(command)
    return DocumentRead.model_validate(entity)


@router.get("", response_model=list[DocumentRead])
async def list_document(
    limit: int = 100,
    offset: int = 0,
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentRead]:
    items = await service.list(limit=limit, offset=offset)
    return [DocumentRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=DocumentRead)
async def get_document(
    item_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    entity = await service.get(item_id)
    return DocumentRead.model_validate(entity)
