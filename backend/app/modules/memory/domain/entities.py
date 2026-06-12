from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class MemoryItem(BaseEntity):
    memory_type: str | None = None
    content: str | None = None
    importance_score: int | None = None
