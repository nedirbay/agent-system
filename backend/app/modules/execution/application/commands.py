from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateExecutionRunCommand:
    task_id: uuid.UUID | None = None
    command: str | None = None
    status: str = "pending"
    output: str | None = None
