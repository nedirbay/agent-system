from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError, NotFoundError
from app.main import app
from app.modules.agents.application.document_agent import (
    DocumentAgentResult,
    DocumentAgentService,
)
from app.modules.agents.presentation.dependencies import get_document_agent_service
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


@pytest.mark.asyncio
async def test_document_agent_analyzes_and_persists_document_metadata() -> None:
    document = Document(
        file_name="contract.pdf",
        mime_type="application/pdf",
        status="parsed",
        page_count=2,
        extracted_text=(
            "This agreement defines payment terms and compliance obligations. "
            "The contract includes a liability clause and risk controls. "
            "The report summary highlights contract risk and payment exposure."
        ),
        doc_metadata={"content": {"language": "en"}},
    )
    repo = MemoryDocumentRepository([document])

    result = await DocumentAgentService(repo).analyze(document.id)

    assert result.document_id == document.id
    assert result.language == "en"
    assert result.classification == "legal"
    assert result.categories[:2] == ["legal", "finance"]
    assert "agreement" in result.summary.lower()
    assert result.metadata["page_count"] == 2
    assert "contract" in result.metadata["top_terms"]
    saved = await repo.get(document.id)
    assert saved is not None
    assert saved.status == "analyzed"
    assert saved.doc_metadata["document_agent"]["classification"] == "legal"


@pytest.mark.asyncio
async def test_document_agent_requires_existing_parsed_text() -> None:
    repo = MemoryDocumentRepository([Document(file_name="empty.txt", status="uploaded")])
    service = DocumentAgentService(repo)
    document_id = next(iter(repo.items))

    with pytest.raises(AppError):
        await service.analyze(document_id)

    with pytest.raises(NotFoundError):
        await service.analyze(uuid.uuid4())


def test_document_agent_endpoint_returns_analysis() -> None:
    document_id = uuid.uuid4()

    class FakeDocumentAgentService:
        async def analyze(self, _document_id: uuid.UUID) -> DocumentAgentResult:
            assert _document_id == document_id
            return DocumentAgentResult(
                document_id=document_id,
                file_name="report.txt",
                summary="Short report summary.",
                language="en",
                categories=["report"],
                classification="report",
                metadata={"word_count": 3},
            )

    app.dependency_overrides[get_document_agent_service] = FakeDocumentAgentService
    try:
        client = TestClient(app)
        response = client.post(
            f"/api/v1/agents/document-agent/documents/{document_id}/analyze"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "document_id": str(document_id),
        "file_name": "report.txt",
        "summary": "Short report summary.",
        "language": "en",
        "categories": ["report"],
        "classification": "report",
        "metadata": {"word_count": 3},
    }
