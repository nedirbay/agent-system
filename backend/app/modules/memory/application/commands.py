from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateMemoryItemCommand:
    memory_type: str | None = None
    content: str | None = None
    importance_score: int | None = None
