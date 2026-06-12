from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.documents.domain.entities import Document


class DocumentRepository(AbstractRepository[Document], ABC):
    """Persistence port for Document aggregates."""
