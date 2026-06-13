from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError, NotFoundError
from app.main import app
from app.modules.analysis.domain.entities import AnalysisJob
from app.modules.analysis.domain.repositories import AnalysisJobRepository
from app.modules.reports.application.report_agent import ReportAgentResult, ReportAgentService
from app.modules.reports.domain.entities import Report
from app.modules.reports.domain.repositories import ReportRepository
from app.modules.reports.presentation.dependencies import get_report_agent_service


class MemoryAnalysisJobRepository(AnalysisJobRepository):
    def __init__(self, jobs: list[AnalysisJob] | None = None) -> None:
        self.items = {j.id: j for j in jobs or []}

    async def add(self, entity: AnalysisJob) -> AnalysisJob:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> AnalysisJob | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AnalysisJob]:
        return list(self.items.values())[offset : offset + limit]


class MemoryReportRepository(ReportRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Report] = {}

    async def add(self, entity: Report) -> Report:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> Report | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Report]:
        return list(self.items.values())[offset : offset + limit]


def _job() -> AnalysisJob:
    return AnalysisJob(
        kind="document_analysis",
        status="completed",
        result={
            "summary": "Analyzed 2 documents with 12 total words.",
            "statistics": {
                "document_count": 2,
                "languages": {"en": 2},
                "top_terms": ["risk", "system"],
            },
            "trends": ["Dominant category is legal."],
            "findings": ["Average document length is 6 words."],
            "recommendations": ["Index analyzed documents in the Knowledge Layer for Q&A."],
        },
    )


@pytest.mark.asyncio
async def test_report_agent_renders_markdown_and_persists() -> None:
    job = _job()
    reports = MemoryReportRepository()
    service = ReportAgentService(
        jobs=MemoryAnalysisJobRepository([job]),
        reports=reports,
    )

    result = await service.generate_from_analysis(job.id, name="Q2 Report")

    assert result.format == "markdown"
    assert result.name == "Q2 Report"
    assert "# Q2 Report" in result.content
    assert "## Summary" in result.content
    assert "## Statistics" in result.content
    assert "- **Document count**: 2" in result.content
    assert "## Trends" in result.content
    assert "## Recommendations" in result.content
    # persisted with body
    saved = await reports.get(result.report_id)
    assert saved is not None
    assert saved.content == result.content
    assert saved.format == "markdown"


@pytest.mark.asyncio
async def test_report_agent_text_format() -> None:
    job = _job()
    service = ReportAgentService(
        jobs=MemoryAnalysisJobRepository([job]),
        reports=MemoryReportRepository(),
    )

    result = await service.generate_from_analysis(job.id, report_format="text")

    assert result.format == "text"
    assert "SUMMARY" in result.content
    assert "STATISTICS" in result.content
    assert "#" not in result.content  # not markdown


@pytest.mark.asyncio
async def test_report_agent_validates_inputs() -> None:
    job = _job()
    service = ReportAgentService(
        jobs=MemoryAnalysisJobRepository([job]),
        reports=MemoryReportRepository(),
    )

    with pytest.raises(NotFoundError):
        await service.generate_from_analysis(uuid.uuid4())

    with pytest.raises(AppError):
        await service.generate_from_analysis(job.id, report_format="pdf")

    empty = AnalysisJob(kind="document_analysis", status="completed", result=None)
    service_empty = ReportAgentService(
        jobs=MemoryAnalysisJobRepository([empty]),
        reports=MemoryReportRepository(),
    )
    with pytest.raises(AppError):
        await service_empty.generate_from_analysis(empty.id)


def test_report_agent_endpoint_returns_result() -> None:
    analysis_job_id = uuid.uuid4()
    report_id = uuid.uuid4()

    class FakeReportAgentService:
        async def generate_from_analysis(
            self, job_id, *, name=None, report_format="markdown", user_id=None
        ) -> ReportAgentResult:
            assert job_id == analysis_job_id
            return ReportAgentResult(
                report_id=report_id,
                analysis_job_id=job_id,
                name="Analysis Report",
                format="markdown",
                content="# Analysis Report\n",
            )

    app.dependency_overrides[get_report_agent_service] = FakeReportAgentService
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/reports/generate-from-analysis",
            json={"analysis_job_id": str(analysis_job_id)},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["report_id"] == str(report_id)
    assert body["format"] == "markdown"
    assert body["content"] == "# Analysis Report\n"
