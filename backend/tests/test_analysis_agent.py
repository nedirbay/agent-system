from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError, NotFoundError
from app.main import app
from app.modules.analysis.application.analysis_agent import (
    AnalysisAgentResult,
    AnalysisAgentService,
)
from app.modules.analysis.domain.entities import AnalysisJob
from app.modules.analysis.domain.repositories import AnalysisJobRepository
from app.modules.analysis.presentation.dependencies import get_analysis_agent_service
from app.modules.documents.domain.entities import Document
from app.modules.documents.domain.repositories import DocumentRepository


class MemoryDocumentRepository(DocumentRepository):
    def __init__(self, documents: list[Document] | None = None) -> None:
        self.items = {d.id: d for d in documents or []}

    async def add(self, entity: Document) -> Document:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> Document | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        return list(self.items.values())[offset : offset + limit]

    async def update(self, entity: Document) -> Document:
        self.items[entity.id] = entity
        return entity


class MemoryAnalysisJobRepository(AnalysisJobRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, AnalysisJob] = {}

    async def add(self, entity: AnalysisJob) -> AnalysisJob:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> AnalysisJob | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AnalysisJob]:
        return list(self.items.values())[offset : offset + limit]


@pytest.mark.asyncio
async def test_analysis_agent_aggregates_documents_and_persists_job() -> None:
    documents = [
        Document(
            file_name="contract.txt",
            extracted_text="Contract risk and payment risk are important.",
            doc_metadata={
                "content": {"language": "en"},
                "document_agent": {"categories": ["legal", "finance"]},
            },
        ),
        Document(
            file_name="architecture.txt",
            extracted_text="System architecture and database deployment notes.",
            doc_metadata={
                "content": {"language": "en"},
                "document_agent": {"categories": ["technical"]},
            },
        ),
    ]
    jobs = MemoryAnalysisJobRepository()
    service = AnalysisAgentService(
        documents=MemoryDocumentRepository(documents),
        jobs=jobs,
    )

    result = await service.analyze_documents([d.id for d in documents])

    assert result.statistics["document_count"] == 2
    assert result.statistics["languages"] == {"en": 2}
    assert result.statistics["categories"] == {"legal": 1, "finance": 1, "technical": 1}
    assert result.statistics["top_terms"][0] == "risk"
    assert "Dominant category" in result.trends[0]
    assert result.recommendations == ["Index analyzed documents in the Knowledge Layer for Q&A."]
    saved = await jobs.get(result.job_id)
    assert saved is not None
    assert saved.status == "completed"
    assert saved.kind == "document_analysis"
    assert saved.result["statistics"]["document_count"] == 2


@pytest.mark.asyncio
async def test_analysis_agent_validates_inputs() -> None:
    service = AnalysisAgentService(
        documents=MemoryDocumentRepository([Document(file_name="empty.txt")]),
        jobs=MemoryAnalysisJobRepository(),
    )

    with pytest.raises(AppError):
        await service.analyze_documents([])

    with pytest.raises(NotFoundError):
        await service.analyze_documents([uuid.uuid4()])

    document_id = next(iter(service._documents.items))  # type: ignore[attr-defined]
    with pytest.raises(AppError):
        await service.analyze_documents([document_id])


def test_analysis_agent_endpoint_returns_result() -> None:
    document_id = uuid.uuid4()
    job_id = uuid.uuid4()

    class FakeAnalysisAgentService:
        async def analyze_documents(self, document_ids: list[uuid.UUID]) -> AnalysisAgentResult:
            assert document_ids == [document_id]
            return AnalysisAgentResult(
                job_id=job_id,
                document_ids=document_ids,
                summary="Analyzed one document.",
                statistics={"document_count": 1},
                trends=["Dataset language is en."],
                findings=["Average document length is 10 words."],
                recommendations=["Index analyzed documents in the Knowledge Layer for Q&A."],
            )

    app.dependency_overrides[get_analysis_agent_service] = FakeAnalysisAgentService
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/analysis/documents/analyze",
            json={"document_ids": [str(document_id)]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "job_id": str(job_id),
        "document_ids": [str(document_id)],
        "summary": "Analyzed one document.",
        "statistics": {"document_count": 1},
        "trends": ["Dataset language is en."],
        "findings": ["Average document length is 10 words."],
        "recommendations": ["Index analyzed documents in the Knowledge Layer for Q&A."],
    }
