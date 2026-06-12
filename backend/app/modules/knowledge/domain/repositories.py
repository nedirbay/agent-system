from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.knowledge.domain.entities import KnowledgeItem


class KnowledgeItemRepository(AbstractRepository[KnowledgeItem], ABC):
    """Persistence port for KnowledgeItem aggregates."""
