from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalysisJobCreate(BaseModel):
    task_id: uuid.UUID | None = None
    kind: str | None = None
    status: str = "pending"
    result: dict | None = None


class AnalysisJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    task_id: uuid.UUID | None = None
    kind: str | None = None
    status: str | None = None
    result: dict | None = None


class AnalyzeDocumentsRequest(BaseModel):
    document_ids: list[uuid.UUID]


class AnalysisAgentResultRead(BaseModel):
    job_id: uuid.UUID
    document_ids: list[uuid.UUID]
    summary: str
    statistics: dict
    trends: list[str]
    findings: list[str]
    recommendations: list[str]
