from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class ExecutionRun(BaseEntity):
    task_id: uuid.UUID | None = None
    command: str | None = None
    status: str | None = "pending"
    output: str | None = None
