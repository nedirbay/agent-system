"""Memory Agent — knowledge management & context assembly (Roadmap Task 20 / AG-009).

The Memory Agent is the single supplier of the `[Memory]` prompt block (ME-001):
it gathers the four memory areas — session (current conversation), long-term
(past tasks), and knowledge (indexed information) — and assembles them into one
ranked, budget-aware context block that the Orchestrator/QA agents drop into
their prompts. Working memory (the current task) is passed in by the caller.

Each area degrades independently (FH-001): a missing session id, an empty
long-term store, or an unavailable knowledge retriever simply omits that
section rather than failing the whole assembly.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.modules.knowledge.application.commands import SearchQuery, SearchResultItem
from app.modules.memory.application.long_term_memory import (
    LongTermMemoryService,
    RecalledMemory,
)
from app.modules.memory.application.session_memory import SessionMemoryService

_logger = get_logger("memory.agent")
_SNIPPET = 280


class KnowledgeRetriever(Protocol):
    async def search(self, query: SearchQuery) -> list[SearchResultItem]: ...


@dataclass(frozen=True)
class KnowledgeMemory:
    chunk_id: uuid.UUID
    document_id: uuid.UUID | None
    score: float
    snippet: str


@dataclass(frozen=True)
class MemoryContext:
    """The unified [Memory] block plus its structured parts."""

    query: str
    session_id: str | None
    working: str | None
    session: str | None
    long_term: list[RecalledMemory] = field(default_factory=list)
    knowledge: list[KnowledgeMemory] = field(default_factory=list)
    text: str = ""


class MemoryAgentService:
    def __init__(
        self,
        *,
        session: SessionMemoryService,
        long_term: LongTermMemoryService,
        knowledge: KnowledgeRetriever | None = None,
    ) -> None:
        self._session = session
        self._long_term = long_term
        self._knowledge = knowledge

    async def assemble_context(
        self,
        query: str,
        *,
        session_id: str | None = None,
        working: str | None = None,
        top_k: int | None = None,
        memory_type: str | None = None,
        document_id: uuid.UUID | None = None,
    ) -> MemoryContext:
        if not (query or "").strip():
            raise AppError("query must not be empty")
        top_k = top_k or get_settings().memory_recall_top_k

        session_text = await self._session_section(session_id)
        long_term = await self._long_term_section(query, top_k, memory_type)
        knowledge = await self._knowledge_section(query, top_k, document_id)

        return MemoryContext(
            query=query,
            session_id=session_id,
            working=working,
            session=session_text,
            long_term=long_term,
            knowledge=knowledge,
            text=self._render(working, session_text, long_term, knowledge),
        )

    async def _session_section(self, session_id: str | None) -> str | None:
        if not session_id:
            return None
        try:
            ctx = await self._session.get_context(session_id)
        except Exception:  # pragma: no cover - infra failure path
            _logger.warning("memory.session_unavailable", session_id=session_id)
            return None
        return ctx.text or None

    async def _long_term_section(
        self, query: str, top_k: int, memory_type: str | None
    ) -> list[RecalledMemory]:
        try:
            return await self._long_term.recall(
                query, top_k=top_k, memory_type=memory_type
            )
        except Exception:  # pragma: no cover - infra failure path
            _logger.warning("memory.long_term_unavailable")
            return []

    async def _knowledge_section(
        self, query: str, top_k: int, document_id: uuid.UUID | None
    ) -> list[KnowledgeMemory]:
        if self._knowledge is None:
            return []
        try:
            hits = await self._knowledge.search(
                SearchQuery(query=query, top_k=top_k, document_id=document_id)
            )
        except Exception:  # pragma: no cover - infra failure path
            _logger.warning("memory.knowledge_unavailable")
            return []
        return [
            KnowledgeMemory(
                chunk_id=h.chunk_id,
                document_id=h.document_id,
                score=h.score,
                snippet=_snippet(h.content),
            )
            for h in hits
        ]

    @staticmethod
    def _render(
        working: str | None,
        session: str | None,
        long_term: list[RecalledMemory],
        knowledge: list[KnowledgeMemory],
    ) -> str:
        sections: list[str] = []
        if working:
            sections.append(f"## Working memory (current task)\n{working.strip()}")
        if session:
            sections.append(f"## Session memory (current conversation)\n{session}")
        if long_term:
            lines = [
                f"- [{m.memory_type or 'memory'}] {m.content}" for m in long_term
            ]
            sections.append("## Long-term memory (past tasks)\n" + "\n".join(lines))
        if knowledge:
            lines = [
                f"[{i}] {k.snippet}" for i, k in enumerate(knowledge, start=1)
            ]
            sections.append("## Knowledge memory (indexed information)\n" + "\n".join(lines))
        return "\n\n".join(sections)


def _snippet(text: str) -> str:
    text = (text or "").strip()
    if len(text) <= _SNIPPET:
        return text
    return text[: _SNIPPET - 1].rstrip() + "…"
