from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class MemoryItem(BaseEntity):
    memory_type: str | None = None
    content: str | None = None
    importance_score: int | None = None


@dataclass
class MemoryReference(BaseEntity):
    """Link between a long-term memory and the entity it was derived from
    (MEMORY_REFERENCES) — e.g. the task, document, or analysis job."""

    memory_id: uuid.UUID | None = None
    related_entity_type: str | None = None
    related_entity_id: uuid.UUID | None = None
