from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.main import app
from app.modules.knowledge.application.commands import SearchQuery, SearchResultItem
from app.modules.knowledge.infrastructure.embedding import HashingEmbeddingProvider
from app.modules.memory.application.long_term_memory import (
    LongTermMemoryService,
    MemoryRef,
)
from app.modules.memory.application.memory_agent import MemoryAgentService
from app.modules.memory.application.session_memory import SessionMemoryService
from app.modules.memory.domain.entities import MemoryItem, MemoryReference
from app.modules.memory.domain.repositories import (
    MemoryItemRepository,
    MemoryReferenceRepository,
)
from app.modules.memory.infrastructure.memory_vector import InMemoryMemoryVectorIndex
from app.modules.memory.infrastructure.session_store import InMemorySessionMemoryStore
from app.modules.memory.presentation.dependencies import (
    get_long_term_memory_service,
    get_memory_agent_service,
    get_session_memory_service,
)


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #


class MemoryItemRepo(MemoryItemRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, MemoryItem] = {}

    async def add(self, entity: MemoryItem) -> MemoryItem:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> MemoryItem | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[MemoryItem]:
        return list(self.items.values())[offset : offset + limit]

    async def list_recent(
        self, *, memory_type: str | None = None, limit: int = 20
    ) -> list[MemoryItem]:
        items = sorted(self.items.values(), key=lambda i: i.created_at, reverse=True)
        if memory_type is not None:
            items = [i for i in items if i.memory_type == memory_type]
        return items[:limit]


class MemoryRefRepo(MemoryReferenceRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, MemoryReference] = {}

    async def add(self, entity: MemoryReference) -> MemoryReference:
        self.items[entity.id] = entity
        return entity

    async def get(self, entity_id: uuid.UUID) -> MemoryReference | None:
        return self.items.get(entity_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[MemoryReference]:
        return list(self.items.values())[offset : offset + limit]

    async def list_for_memory(self, memory_id: uuid.UUID) -> list[MemoryReference]:
        return [r for r in self.items.values() if r.memory_id == memory_id]


def _long_term_service() -> LongTermMemoryService:
    return LongTermMemoryService(
        items=MemoryItemRepo(),
        references=MemoryRefRepo(),
        embedder=HashingEmbeddingProvider(),
        vectors=InMemoryMemoryVectorIndex(),
    )


# --------------------------------------------------------------------------- #
# Task 18 — Session memory
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_session_memory_appends_and_assembles_context() -> None:
    service = SessionMemoryService(InMemorySessionMemoryStore())

    await service.append_turn("s1", "user", "What is the refund policy?")
    ctx = await service.append_turn("s1", "assistant", "Refunds within 30 days.")

    assert len(ctx.turns) == 2
    assert ctx.turns[0].role == "user"
    assert "Recent turns:" in ctx.text
    assert "refund policy" in ctx.text


@pytest.mark.asyncio
async def test_session_memory_compresses_old_turns() -> None:
    service = SessionMemoryService(
        InMemorySessionMemoryStore(), max_turns=4, recent_turns=2
    )
    for i in range(6):
        await service.append_turn("s1", "user", f"message number {i}")

    ctx = await service.get_context("s1")
    # Compression fires when the count exceeds max_turns (4), trimming to the
    # recent 2 and folding the rest into the summary; turns then regrow up to
    # the threshold again. After 6 appends: summary holds 0-2, turns hold 3-5.
    assert len(ctx.turns) == 3
    assert ctx.turns[-1].content == "message number 5"
    assert ctx.turns[0].content == "message number 3"
    assert ctx.summary is not None
    assert "message number 0" in ctx.summary
    assert "message number 2" in ctx.summary
    assert "Earlier conversation summary:" in ctx.text


@pytest.mark.asyncio
async def test_session_memory_validates_input() -> None:
    service = SessionMemoryService(InMemorySessionMemoryStore())
    with pytest.raises(AppError):
        await service.append_turn("s1", "robot", "hi")
    with pytest.raises(AppError):
        await service.append_turn("s1", "user", "   ")
    with pytest.raises(AppError):
        await service.append_turn("", "user", "hi")


@pytest.mark.asyncio
async def test_session_memory_clear() -> None:
    store = InMemorySessionMemoryStore()
    service = SessionMemoryService(store)
    await service.append_turn("s1", "user", "remember me")
    await service.clear("s1")
    ctx = await service.get_context("s1")
    assert ctx.turns == []
    assert ctx.text == ""


# --------------------------------------------------------------------------- #
# Task 19 — Long-term memory
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_long_term_remember_and_semantic_recall() -> None:
    service = _long_term_service()

    await service.remember(
        "The customer prefers email communication over phone calls.",
        memory_type="preference",
        importance_score=8,
    )
    await service.remember(
        "The invoice for project Apollo was paid in full.",
        memory_type="fact",
        importance_score=3,
    )

    results = await service.recall("how should we contact the customer?", top_k=2)

    assert results
    # The preference memory is the most lexically/semantically similar.
    assert "email communication" in results[0].content
    assert results[0].memory_type == "preference"


@pytest.mark.asyncio
async def test_long_term_remember_persists_references() -> None:
    items = MemoryItemRepo()
    refs = MemoryRefRepo()
    service = LongTermMemoryService(
        items=items,
        references=refs,
        embedder=HashingEmbeddingProvider(),
        vectors=InMemoryMemoryVectorIndex(),
    )
    doc_id = uuid.uuid4()

    item = await service.remember(
        "Document summary stored as memory.",
        memory_type="summary",
        references=[MemoryRef(related_entity_type="document", related_entity_id=doc_id)],
    )

    stored_refs = await refs.list_for_memory(item.id)
    assert len(stored_refs) == 1
    assert stored_refs[0].related_entity_type == "document"
    assert stored_refs[0].related_entity_id == doc_id

    recalled = await service.recall("document summary", top_k=1)
    assert recalled[0].references[0].related_entity_type == "document"


@pytest.mark.asyncio
async def test_long_term_validates_input() -> None:
    service = _long_term_service()
    with pytest.raises(AppError):
        await service.remember("   ")
    with pytest.raises(AppError):
        await service.remember("ok", importance_score=99)
    with pytest.raises(AppError):
        await service.recall("  ")


@pytest.mark.asyncio
async def test_long_term_recall_degrades_to_recent_when_index_fails() -> None:
    class BrokenIndex(InMemoryMemoryVectorIndex):
        async def search(self, *a, **k):  # type: ignore[override]
            raise RuntimeError("qdrant down")

    items = MemoryItemRepo()
    service = LongTermMemoryService(
        items=items,
        references=MemoryRefRepo(),
        embedder=HashingEmbeddingProvider(),
        vectors=BrokenIndex(),
    )
    await service.remember("a durable fact", memory_type="fact")

    results = await service.recall("anything")
    assert len(results) == 1
    assert results[0].content == "a durable fact"
    assert results[0].score == 0.0  # fallback path, no similarity score


# --------------------------------------------------------------------------- #
# Task 20 — Memory Agent context assembly
# --------------------------------------------------------------------------- #


class FakeRetriever:
    async def search(self, query: SearchQuery) -> list[SearchResultItem]:
        return [
            SearchResultItem(
                chunk_id=uuid.uuid4(),
                document_id=uuid.uuid4(),
                chunk_index=0,
                score=0.91,
                page=1,
                content="Indexed knowledge about the refund policy.",
            )
        ]


@pytest.mark.asyncio
async def test_memory_agent_assembles_all_sections() -> None:
    session = SessionMemoryService(InMemorySessionMemoryStore())
    await session.append_turn("s1", "user", "Tell me about refunds.")

    long_term = _long_term_service()
    await long_term.remember(
        "Refund requests are handled by the finance team.",
        memory_type="fact",
        importance_score=5,
    )

    agent = MemoryAgentService(
        session=session, long_term=long_term, knowledge=FakeRetriever()
    )

    ctx = await agent.assemble_context(
        "refund policy", session_id="s1", working="Drafting a refund FAQ."
    )

    assert "Working memory" in ctx.text
    assert "Session memory" in ctx.text
    assert "Long-term memory" in ctx.text
    assert "Knowledge memory" in ctx.text
    assert ctx.long_term
    assert ctx.knowledge


@pytest.mark.asyncio
async def test_memory_agent_omits_unavailable_sections() -> None:
    agent = MemoryAgentService(
        session=SessionMemoryService(InMemorySessionMemoryStore()),
        long_term=_long_term_service(),
        knowledge=None,
    )
    # No session id, empty long-term store, no knowledge retriever.
    ctx = await agent.assemble_context("anything")
    assert ctx.session is None
    assert ctx.long_term == []
    assert ctx.knowledge == []
    assert ctx.text == ""


@pytest.mark.asyncio
async def test_memory_agent_validates_query() -> None:
    agent = MemoryAgentService(
        session=SessionMemoryService(InMemorySessionMemoryStore()),
        long_term=_long_term_service(),
    )
    with pytest.raises(AppError):
        await agent.assemble_context("   ")


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


def test_memory_endpoints_session_long_term_and_context() -> None:
    session_store = InMemorySessionMemoryStore()
    session_service = SessionMemoryService(session_store)
    long_term = _long_term_service()
    agent = MemoryAgentService(
        session=session_service, long_term=long_term, knowledge=FakeRetriever()
    )

    app.dependency_overrides[get_session_memory_service] = lambda: session_service
    app.dependency_overrides[get_long_term_memory_service] = lambda: long_term
    app.dependency_overrides[get_memory_agent_service] = lambda: agent
    try:
        client = TestClient(app)

        # Session turn
        r = client.post(
            "/api/v1/memory/sessions/abc/turns",
            json={"role": "user", "content": "Hello there"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["session_id"] == "abc"

        # Remember
        r = client.post(
            "/api/v1/memory/long-term",
            json={"content": "Important fact", "memory_type": "fact", "importance_score": 7},
        )
        assert r.status_code == 201, r.text

        # Recall
        r = client.post("/api/v1/memory/long-term/recall", json={"query": "fact"})
        assert r.status_code == 200, r.text
        assert any("Important fact" in m["content"] for m in r.json())

        # Assemble unified context
        r = client.post(
            "/api/v1/memory/context",
            json={"query": "fact", "session_id": "abc"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["session"] is not None
        assert body["knowledge"]

        # Clear session
        r = client.delete("/api/v1/memory/sessions/abc")
        assert r.status_code == 204
    finally:
        app.dependency_overrides.clear()
