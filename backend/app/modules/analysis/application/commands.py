from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateAnalysisJobCommand:
    task_id: uuid.UUID | None = None
    kind: str | None = None
    status: str = "pending"
    result: dict | None = None
