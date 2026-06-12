"""Abstract repository port shared by every module (dependency inversion).

The domain/application layers depend on this interface; concrete SQLAlchemy
implementations live in each module's infrastructure layer.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

E = TypeVar("E")


class AbstractRepository(ABC, Generic[E]):
    @abstractmethod
    async def add(self, entity: E) -> E: ...

    @abstractmethod
    async def get(self, entity_id: uuid.UUID) -> E | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[E]: ...
