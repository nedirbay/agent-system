from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.shared.domain.entity import BaseEntity


@dataclass
class AnalysisJob(BaseEntity):
    task_id: uuid.UUID | None = None
    kind: str | None = None
    status: str | None = "pending"
    result: dict | None = None
