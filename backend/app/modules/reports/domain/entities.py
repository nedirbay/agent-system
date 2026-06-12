from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class Report(BaseEntity):
    user_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    name: str | None = None
    format: str | None = None
    storage_path: str | None = None
