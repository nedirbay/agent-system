from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.main import app
from app.modules.knowledge.application.commands import SearchQuery, SearchResultItem
from app.modules.qa.application.qa_agent import QaAgentService, QaAnswer
from app.modules.qa.presentation.dependencies import get_qa_agent_service
from app.shared.llm import ChatMessage, CompletionResult


def _hit(content: str, *, score: float = 0.9, index: int = 0) -> SearchResultItem:
    return SearchResultItem(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        chunk_index=index,
        score=score,
        page=1,
        content=content,
    )


class FakeRetriever:
    def __init__(self, hits: list[SearchResultItem]) -> None:
        self.hits = hits
        self.last_query: SearchQuery | None = None

    async def search(self, query: SearchQuery) -> list[SearchResultItem]:
        self.last_query = query
        return self.hits


class FakeLLM:
    def __init__(self, *, text: str = "", raises: bool = False) -> None:
        self._text = text
        self._raises = raises

    async def complete(self, messages: list[ChatMessage], **kwargs) -> CompletionResult:
        if self._raises:
            raise RuntimeError("llm down")
        return CompletionResult(text=self._text, model="fake")

    async def complete_json(self, messages, **kwargs) -> dict:  # pragma: no cover
        return {}


@pytest.mark.asyncio
async def test_qa_agent_answers_grounded_with_citations() -> None:
    retriever = FakeRetriever([_hit("The capital of France is Paris.", index=0)])
    service = QaAgentService(
        retriever=retriever,
        llm=FakeLLM(text="The capital is Paris [1]."),
    )

    result = await service.ask("What is the capital of France?", top_k=3)

    assert result.grounded is True
    assert result.llm_used is True
    assert result.answer == "The capital is Paris [1]."
    assert len(result.citations) == 1
    assert result.citations[0].index == 1
    assert result.citations[0].snippet == "The capital of France is Paris."
    # the question is passed through to retrieval with top_k
    assert retriever.last_query is not None
    assert retriever.last_query.top_k == 3


@pytest.mark.asyncio
async def test_qa_agent_refuses_without_retrieval() -> None:
    service = QaAgentService(retriever=FakeRetriever([]), llm=FakeLLM(text="ignored"))

    result = await service.ask("Anything?")

    assert result.grounded is False
    assert result.llm_used is False
    assert result.citations == []
    assert "don't have enough" in result.answer


@pytest.mark.asyncio
async def test_qa_agent_falls_back_to_extractive_when_llm_unavailable() -> None:
    retriever = FakeRetriever([_hit("Solar panels convert sunlight into electricity.")])
    service = QaAgentService(retriever=retriever, llm=FakeLLM(raises=True))

    result = await service.ask("How do solar panels work?")

    assert result.grounded is True
    assert result.llm_used is False
    assert "Solar panels convert sunlight into electricity." in result.answer
    assert "[1]" in result.answer


@pytest.mark.asyncio
async def test_qa_agent_rejects_empty_question() -> None:
    service = QaAgentService(retriever=FakeRetriever([]), llm=FakeLLM())
    with pytest.raises(AppError):
        await service.ask("   ")


def test_qa_agent_endpoint_returns_answer() -> None:
    class FakeQaAgentService:
        async def ask(self, question, *, top_k=5, document_id=None) -> QaAnswer:
            return QaAnswer(
                question=question,
                answer="Paris [1].",
                grounded=True,
                llm_used=True,
                citations=[],
            )

    app.dependency_overrides[get_qa_agent_service] = FakeQaAgentService
    try:
        client = TestClient(app)
        response = client.post("/api/v1/qa/ask", json={"question": "Capital of France?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Paris [1]."
    assert body["grounded"] is True
    assert body["citations"] == []
