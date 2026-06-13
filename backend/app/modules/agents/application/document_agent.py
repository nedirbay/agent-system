from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass, field

from app.core.exceptions import AppError, NotFoundError
from app.modules.documents.domain.entities import Document
from app.modules.documents.domain.repositories import DocumentRepository

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD_RE = re.compile(r"[\w'-]+", re.UNICODE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "we",
    "with",
}

_CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "legal": {"agreement", "contract", "clause", "liability", "compliance", "risk"},
    "finance": {"invoice", "budget", "revenue", "cost", "payment", "tax", "total"},
    "technical": {"api", "database", "system", "architecture", "deployment", "server"},
    "research": {"study", "method", "finding", "analysis", "evidence", "result"},
    "operations": {"process", "workflow", "schedule", "inventory", "logistics"},
    "hr": {"employee", "policy", "leave", "salary", "hiring", "training"},
    "report": {"report", "summary", "recommendation", "overview", "appendix"},
}


@dataclass(frozen=True)
class DocumentAgentResult:
    document_id: uuid.UUID
    file_name: str | None
    summary: str
    language: str | None
    categories: list[str] = field(default_factory=list)
    classification: str = "general"
    metadata: dict = field(default_factory=dict)


class DocumentAgentService:
    """Specialized Document Agent (Roadmap Task 14).

    The ingestion layer already owns file parsing/OCR/metadata extraction. This
    agent consumes that parsed text and performs document-level analysis:
    summarization, category detection, and classification.
    """

    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    async def analyze(self, document_id: uuid.UUID) -> DocumentAgentResult:
        document = await self._documents.get(document_id)
        if document is None:
            raise NotFoundError("Document not found")
        if not document.extracted_text or not document.extracted_text.strip():
            raise AppError("Document must be parsed before Document Agent analysis")

        result = self._analyze(document)
        document.doc_metadata = {
            **(document.doc_metadata or {}),
            "document_agent": {
                "summary": result.summary,
                "language": result.language,
                "categories": result.categories,
                "classification": result.classification,
                "metadata": result.metadata,
            },
        }
        document.status = "analyzed"
        await self._documents.update(document)
        return result

    def _analyze(self, document: Document) -> DocumentAgentResult:
        text = document.extracted_text or ""
        words = [w.lower() for w in _WORD_RE.findall(text)]
        meaningful = [w for w in words if w not in _STOPWORDS and len(w) > 2]
        categories = self._categories(meaningful)
        language = self._language(document)
        return DocumentAgentResult(
            document_id=document.id,
            file_name=document.file_name,
            summary=self._summary(text, meaningful),
            language=language,
            categories=categories,
            classification=categories[0] if categories else self._fallback_classification(document),
            metadata={
                "char_count": len(text),
                "word_count": len(words),
                "sentence_count": len(self._sentences(text)),
                "page_count": document.page_count,
                "top_terms": [term for term, _ in Counter(meaningful).most_common(8)],
            },
        )

    def _summary(self, text: str, meaningful: list[str]) -> str:
        sentences = self._sentences(text)
        if not sentences:
            return ""
        if len(sentences) <= 2:
            return " ".join(sentences)

        frequencies = Counter(meaningful)
        scored = []
        for idx, sentence in enumerate(sentences):
            terms = [w.lower() for w in _WORD_RE.findall(sentence)]
            score = sum(frequencies.get(term, 0) for term in terms)
            scored.append((score, idx, sentence))

        selected = sorted(scored, key=lambda item: (-item[0], item[1]))[:3]
        return " ".join(sentence for _, _, sentence in sorted(selected, key=lambda item: item[1]))

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]

    @staticmethod
    def _categories(terms: list[str]) -> list[str]:
        counts = Counter(terms)
        scored = []
        for category, keywords in _CATEGORY_KEYWORDS.items():
            score = sum(counts.get(keyword, 0) for keyword in keywords)
            if score:
                scored.append((score, category))
        return [category for _, category in sorted(scored, key=lambda item: (-item[0], item[1]))]

    @staticmethod
    def _language(document: Document) -> str | None:
        meta = document.doc_metadata or {}
        content = meta.get("content") if isinstance(meta.get("content"), dict) else {}
        language = content.get("language")
        return language if isinstance(language, str) else None

    @staticmethod
    def _fallback_classification(document: Document) -> str:
        mime = (document.mime_type or "").lower()
        name = (document.file_name or "").lower()
        if "spreadsheet" in mime or name.endswith((".xlsx", ".xlsm", ".csv")):
            return "spreadsheet"
        if "pdf" in mime or name.endswith(".pdf"):
            return "document"
        return "general"
