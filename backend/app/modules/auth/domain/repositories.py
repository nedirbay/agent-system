from __future__ import annotations

from abc import ABC, abstractmethod

from app.shared.domain.repository import AbstractRepository
from app.modules.auth.domain.entities import User


class UserRepository(AbstractRepository[User], ABC):
    """Persistence port for User aggregates."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...
