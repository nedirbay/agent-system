from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.qa.domain.entities import QaConversation


class QaConversationRepository(AbstractRepository[QaConversation], ABC):
    """Persistence port for QaConversation aggregates."""
