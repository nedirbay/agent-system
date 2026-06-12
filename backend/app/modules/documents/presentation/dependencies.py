from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.documents.application.services import DocumentService
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository


def get_document_service(session: AsyncSession = Depends(get_session)) -> DocumentService:
    return DocumentService(SqlAlchemyDocumentRepository(session))
