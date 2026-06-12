from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.modules.documents.application.commands import (
    CreateDocumentCommand,
    UploadDocumentCommand,
)
from app.modules.documents.application.services import DocumentService
from app.modules.documents.presentation.dependencies import get_document_service
from app.modules.documents.presentation.schemas import (
    DocumentCreate,
    DocumentRead,
    DownloadUrlResponse,
    ParseResult,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentRead, status_code=201)
async def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    command = CreateDocumentCommand(**payload.model_dump())
    entity = await service.create(command)
    return DocumentRead.model_validate(entity)


@router.post("/upload", response_model=DocumentRead, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user_id: uuid.UUID | None = Form(default=None),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    """Upload a real file — stored in MinIO, recorded in the database."""
    content = await file.read()
    command = UploadDocumentCommand(
        file_name=file.filename or "unnamed",
        content=content,
        mime_type=file.content_type,
        user_id=user_id,
    )
    entity = await service.upload(command)
    return DocumentRead.model_validate(entity)


@router.post("/{item_id}/parse", response_model=ParseResult)
async def parse_document(
    item_id: uuid.UUID,
    preview_chars: int = 500,
    service: DocumentService = Depends(get_document_service),
) -> ParseResult:
    """Extract text from the stored file (PDF/DOCX/XLSX/image/text) and save it.

    Scanned PDFs and image files are run through OCR (Tesseract) automatically.
    """
    outcome = await service.parse(item_id)
    doc = outcome.document
    text = doc.extracted_text or ""
    return ParseResult(
        id=doc.id,
        status=doc.status,
        page_count=doc.page_count,
        char_count=outcome.char_count,
        ocr_used=outcome.ocr_used,
        doc_metadata=doc.doc_metadata,
        text_preview=text[:preview_chars],
    )


@router.get("/{item_id}/download-url", response_model=DownloadUrlResponse)
async def get_download_url(
    item_id: uuid.UUID,
    expires: int = 3600,
    service: DocumentService = Depends(get_document_service),
) -> DownloadUrlResponse:
    """Time-limited URL to download the file straight from object storage."""
    url = await service.get_download_url(item_id, expires_seconds=expires)
    return DownloadUrlResponse(url=url, expires_in=expires)


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
