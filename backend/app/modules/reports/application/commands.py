from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateReportCommand:
    name: str
    user_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    format: str | None = None
    storage_path: str | None = None
