from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.documents.application.services import DocumentService
from app.modules.documents.infrastructure.metadata import CompositeMetadataExtractor
from app.modules.documents.infrastructure.ocr import TesseractOcrEngine
from app.modules.documents.infrastructure.parser import MultiFormatDocumentParser
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository
from app.modules.documents.infrastructure.storage import MinioFileStorage


def get_document_service(session: AsyncSession = Depends(get_session)) -> DocumentService:
    return DocumentService(
        SqlAlchemyDocumentRepository(session),
        MinioFileStorage(),
        MultiFormatDocumentParser(ocr=TesseractOcrEngine()),
        CompositeMetadataExtractor(),
    )
