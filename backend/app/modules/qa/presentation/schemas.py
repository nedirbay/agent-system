from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QaConversationCreate(BaseModel):
    user_id: uuid.UUID | None = None
    title: str | None = None


class QaConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID | None = None
    title: str | None = None


class QaAskRequest(BaseModel):
    question: str
    top_k: int = 5
    document_id: uuid.UUID | None = None


class QaCitationRead(BaseModel):
    index: int
    chunk_id: uuid.UUID
    document_id: uuid.UUID | None = None
    chunk_index: int | None = None
    page: int | None = None
    score: float
    snippet: str


class QaAnswerRead(BaseModel):
    question: str
    answer: str
    grounded: bool
    llm_used: bool
    citations: list[QaCitationRead]
