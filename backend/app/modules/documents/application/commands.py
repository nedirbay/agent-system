from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class CreateDocumentCommand:
    file_name: str
    user_id: uuid.UUID | None = None
    mime_type: str | None = None
    size: int | None = None
    storage_path: str | None = None
    status: str = "uploaded"
