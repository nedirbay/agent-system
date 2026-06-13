"""Specialized Q&A Agent (Roadmap Task 16) — RAG (LLM_AND_RAG_STRATEGY.md).

Answers a natural-language question grounded in the indexed knowledge base:

    question → embed + vector search (retrieval) → build cited context →
    LLM answer constrained to that context.

Grounding rules:
- If retrieval returns nothing, the agent refuses instead of hallucinating.
- The LLM is instructed to answer ONLY from the supplied context and cite
  sources as ``[n]``.
- If the LLM is unavailable (FH-001 graceful degradation), the agent falls back
  to an extractive answer built from the top retrieved chunks, so the endpoint
  still returns a useful, grounded response.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol

from app.core.exceptions import AppError
from app.modules.knowledge.application.commands import SearchQuery, SearchResultItem
from app.shared.llm import ChatMessage, LLMProvider

_SYSTEM = (
    "You are the Q&A Agent of a multi-agent platform. Answer the user's question "
    "using ONLY the numbered context passages provided. Cite the passages you rely "
    "on as [1], [2], etc. If the context does not contain the answer, say you do "
    "not have enough information — never invent facts. Keep the answer concise."
)

_REFUSAL = (
    "I don't have enough indexed information to answer that. "
    "Index relevant documents in the Knowledge Layer first."
)

_SNIPPET_LIMIT = 280


class Retriever(Protocol):
    """Retrieval port — satisfied by ``KnowledgeIndexService``."""

    async def search(self, query: SearchQuery) -> list[SearchResultItem]: ...


@dataclass(frozen=True)
class Citation:
    index: int  # 1-based marker used in the answer text ([1], [2], ...)
    chunk_id: uuid.UUID
    document_id: uuid.UUID | None
    chunk_index: int | None
    page: int | None
    score: float
    snippet: str


@dataclass(frozen=True)
class QaAnswer:
    question: str
    answer: str
    grounded: bool
    llm_used: bool
    citations: list[Citation] = field(default_factory=list)


class QaAgentService:
    def __init__(self, *, retriever: Retriever, llm: LLMProvider) -> None:
        self._retriever = retriever
        self._llm = llm

    async def ask(
        self,
        question: str,
        *,
        top_k: int = 5,
        document_id: uuid.UUID | None = None,
    ) -> QaAnswer:
        if not question or not question.strip():
            raise AppError("Question must not be empty")

        hits = await self._retriever.search(
            SearchQuery(query=question, top_k=top_k, document_id=document_id)
        )
        if not hits:
            return QaAnswer(
                question=question,
                answer=_REFUSAL,
                grounded=False,
                llm_used=False,
                citations=[],
            )

        citations = self._citations(hits)
        try:
            answer = await self._generate(question, hits)
            llm_used = True
        except Exception:  # FH-001: degrade to an extractive answer, stay grounded
            answer = self._extractive(citations)
            llm_used = False

        return QaAnswer(
            question=question,
            answer=answer,
            grounded=True,
            llm_used=llm_used,
            citations=citations,
        )

    async def _generate(self, question: str, hits: list[SearchResultItem]) -> str:
        context = "\n\n".join(
            f"[{i}] {hit.content.strip()}" for i, hit in enumerate(hits, start=1)
        )
        user = f"Context:\n{context}\n\nQuestion: {question}"
        result = await self._llm.complete(
            [ChatMessage("system", _SYSTEM), ChatMessage("user", user)]
        )
        text = (result.text or "").strip()
        if not text:
            raise AppError("LLM returned an empty answer")
        return text

    @staticmethod
    def _citations(hits: list[SearchResultItem]) -> list[Citation]:
        return [
            Citation(
                index=i,
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                chunk_index=hit.chunk_index,
                page=hit.page,
                score=hit.score,
                snippet=_snippet(hit.content),
            )
            for i, hit in enumerate(hits, start=1)
        ]

    @staticmethod
    def _extractive(citations: list[Citation]) -> str:
        top = citations[:3]
        body = " ".join(f"{c.snippet} [{c.index}]" for c in top)
        return f"Based on the retrieved passages: {body}".strip()


def _snippet(content: str) -> str:
    text = " ".join((content or "").split())
    if len(text) <= _SNIPPET_LIMIT:
        return text
    return text[:_SNIPPET_LIMIT].rstrip() + "…"
