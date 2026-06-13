from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemoryItemCreate(BaseModel):
    memory_type: str | None = None
    content: str | None = None
    importance_score: int | None = None


class MemoryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    memory_type: str | None = None
    content: str | None = None
    importance_score: int | None = None


# --- Session memory (Task 18) ---


class SessionTurnRead(BaseModel):
    role: str
    content: str
    created_at: datetime


class AppendTurnRequest(BaseModel):
    role: str
    content: str


class SessionContextRead(BaseModel):
    session_id: str
    summary: str | None = None
    turns: list[SessionTurnRead] = []
    text: str


# --- Long-term memory (Task 19) ---


class MemoryReferenceIn(BaseModel):
    related_entity_type: str
    related_entity_id: uuid.UUID | None = None


class RememberRequest(BaseModel):
    content: str
    memory_type: str | None = None
    importance_score: int | None = None
    references: list[MemoryReferenceIn] = []


class RecallRequest(BaseModel):
    query: str
    top_k: int | None = None
    memory_type: str | None = None


class MemoryReferenceRead(BaseModel):
    related_entity_type: str
    related_entity_id: uuid.UUID | None = None


class RecalledMemoryRead(BaseModel):
    memory_id: uuid.UUID
    memory_type: str | None = None
    content: str
    importance_score: int | None = None
    score: float
    references: list[MemoryReferenceRead] = []


# --- Memory Agent context assembly (Task 20) ---


class AssembleContextRequest(BaseModel):
    query: str
    session_id: str | None = None
    working: str | None = None
    top_k: int | None = None
    memory_type: str | None = None
    document_id: uuid.UUID | None = None


class KnowledgeMemoryRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID | None = None
    score: float
    snippet: str


class MemoryContextRead(BaseModel):
    query: str
    session_id: str | None = None
    working: str | None = None
    session: str | None = None
    long_term: list[RecalledMemoryRead] = []
    knowledge: list[KnowledgeMemoryRead] = []
    text: str
