from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass

from app.core.exceptions import AppError, NotFoundError
from app.modules.analysis.domain.entities import AnalysisJob
from app.modules.analysis.domain.repositories import AnalysisJobRepository
from app.modules.documents.domain.entities import Document
from app.modules.documents.domain.repositories import DocumentRepository

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


@dataclass(frozen=True)
class AnalysisAgentResult:
    job_id: uuid.UUID
    document_ids: list[uuid.UUID]
    summary: str
    statistics: dict
    trends: list[str]
    findings: list[str]
    recommendations: list[str]


class AnalysisAgentService:
    """Specialized Analysis Agent (Roadmap Task 15).

    Profiles parsed/analyzed documents and persists an AnalysisJob with
    aggregate statistics, simple trends, findings, and recommendations.
    """

    def __init__(
        self,
        *,
        documents: DocumentRepository,
        jobs: AnalysisJobRepository,
    ) -> None:
        self._documents = documents
        self._jobs = jobs

    async def analyze_documents(self, document_ids: list[uuid.UUID]) -> AnalysisAgentResult:
        if not document_ids:
            raise AppError("At least one document_id is required")

        documents: list[Document] = []
        for document_id in document_ids:
            document = await self._documents.get(document_id)
            if document is None:
                raise NotFoundError("Document not found")
            if not document.extracted_text or not document.extracted_text.strip():
                raise AppError("All documents must be parsed before analysis")
            documents.append(document)

        result_payload = self._build_result(documents)
        job = await self._jobs.add(
            AnalysisJob(
                kind="document_analysis",
                status="completed",
                result=result_payload,
            )
        )
        return AnalysisAgentResult(
            job_id=job.id,
            document_ids=document_ids,
            summary=result_payload["summary"],
            statistics=result_payload["statistics"],
            trends=result_payload["trends"],
            findings=result_payload["findings"],
            recommendations=result_payload["recommendations"],
        )

    def _build_result(self, documents: list[Document]) -> dict:
        total_words = 0
        total_chars = 0
        languages: Counter[str] = Counter()
        categories: Counter[str] = Counter()
        terms: Counter[str] = Counter()
        largest: Document | None = None

        for document in documents:
            text = document.extracted_text or ""
            words = _WORD_RE.findall(text)
            meaningful = [w.lower() for w in words if len(w) > 2 and w.lower() not in _STOPWORDS]
            total_words += len(words)
            total_chars += len(text)
            terms.update(meaningful)
            language = self._language(document)
            if language:
                languages[language] += 1
            categories.update(self._categories(document))
            if largest is None or len(text) > len(largest.extracted_text or ""):
                largest = document

        statistics = {
            "document_count": len(documents),
            "total_words": total_words,
            "total_chars": total_chars,
            "average_words_per_document": round(total_words / len(documents), 2),
            "languages": dict(languages),
            "categories": dict(categories),
            "top_terms": [term for term, _ in terms.most_common(10)],
            "largest_document": {
                "id": str(largest.id) if largest else None,
                "file_name": largest.file_name if largest else None,
            },
        }
        trends = self._trends(statistics)
        findings = self._findings(statistics)
        recommendations = self._recommendations(statistics)
        return {
            "summary": self._summary(statistics),
            "statistics": statistics,
            "trends": trends,
            "findings": findings,
            "recommendations": recommendations,
        }

    @staticmethod
    def _language(document: Document) -> str | None:
        meta = document.doc_metadata or {}
        content = meta.get("content") if isinstance(meta.get("content"), dict) else {}
        language = content.get("language")
        return language if isinstance(language, str) else None

    @staticmethod
    def _categories(document: Document) -> list[str]:
        meta = document.doc_metadata or {}
        agent = meta.get("document_agent") if isinstance(meta.get("document_agent"), dict) else {}
        raw = agent.get("categories", [])
        return [c for c in raw if isinstance(c, str)]

    @staticmethod
    def _summary(statistics: dict) -> str:
        return (
            f"Analyzed {statistics['document_count']} documents with "
            f"{statistics['total_words']} total words. "
            f"Top terms: {', '.join(statistics['top_terms'][:5]) or 'none'}."
        )

    @staticmethod
    def _trends(statistics: dict) -> list[str]:
        trends: list[str] = []
        categories = statistics["categories"]
        if categories:
            top_category = max(categories.items(), key=lambda item: item[1])[0]
            trends.append(f"Dominant category is {top_category}.")
        languages = statistics["languages"]
        if len(languages) > 1:
            trends.append("Dataset is multilingual.")
        elif len(languages) == 1:
            trends.append(f"Dataset language is {next(iter(languages))}.")
        return trends

    @staticmethod
    def _findings(statistics: dict) -> list[str]:
        findings = [
            f"Average document length is {statistics['average_words_per_document']} words."
        ]
        if statistics["top_terms"]:
            findings.append(f"Most repeated term is '{statistics['top_terms'][0]}'.")
        if not statistics["categories"]:
            findings.append("No document-agent categories were available.")
        return findings

    @staticmethod
    def _recommendations(statistics: dict) -> list[str]:
        recommendations = []
        if not statistics["categories"]:
            recommendations.append("Run Document Agent classification before deeper analysis.")
        if statistics["document_count"] == 1:
            recommendations.append("Add more documents to identify cross-document trends.")
        if statistics["total_words"] > 0:
            recommendations.append("Index analyzed documents in the Knowledge Layer for Q&A.")
        return recommendations
