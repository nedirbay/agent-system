from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class Document(BaseEntity):
    user_id: uuid.UUID | None = None
    file_name: str | None = None
    mime_type: str | None = None
    size: int | None = None
    storage_path: str | None = None
    status: str | None = "uploaded"
