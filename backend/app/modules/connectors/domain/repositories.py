from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.shared.domain.repository import AbstractRepository
from app.modules.connectors.domain.entities import ConnectorConnection


class ConnectorConnectionRepository(AbstractRepository[ConnectorConnection], ABC):
    """Persistence port for connector connections."""

    @abstractmethod
    async def list_by_user(
        self, user_id: uuid.UUID | None, *, limit: int = 100, offset: int = 0
    ) -> list[ConnectorConnection]: ...

    @abstractmethod
    async def delete(self, entity_id: uuid.UUID) -> bool: ...
