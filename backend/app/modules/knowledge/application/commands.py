from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateKnowledgeItemCommand:
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    title: str | None = None
    content: str | None = None
