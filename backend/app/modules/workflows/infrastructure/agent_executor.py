"""Real-agent step executor (Roadmap Task 13 — closes EX-001 dispatch).

The Orchestrator plans steps against the agent registry; this executor runs each
step by dispatching to the **real specialized agent service** for that
``agent_type`` (DocumentAgent, KnowledgeAgent, AnalysisAgent, QAAgent,
ReportAgent, MemoryAgent, ExecutionAgent) instead of having the LLM role-play the
agent. This is what makes the platform a genuine multi-agent system: one brain
(the Orchestrator) drives many agents that each perform real work.

Each agent needs structured inputs (``document_id``, ``document_ids``,
``analysis_job_id``, ``actions`` …). Those are resolved from the workflow
context — either seeded by the caller on ``WorkflowEngine.run(..., context=...)``
or produced by an earlier step (EX-003 output mapping; e.g. an AnalysisAgent step
emits ``analysis_job_id`` which a later ReportAgent step consumes).

Graceful degradation (FH-001): when a step's required input is unavailable, or
the agent type has no dedicated service yet (CriticAgent, ResearchAgent), the
step falls back to the LLM role-play executor so the workflow still advances.
The :class:`StepExecutor` port and the :class:`WorkflowEngine` are unchanged.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import get_redis
from app.modules.analysis.application.analysis_agent import AnalysisAgentService
from app.modules.analysis.infrastructure.repositories import SqlAlchemyAnalysisJobRepository
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository
from app.modules.execution.application.execution_agent import ExecutionAgentService
from app.modules.execution.application.sandbox import SafeExecutionSandbox
from app.modules.execution.domain.actions import Action
from app.modules.execution.domain.sandbox import SandboxPolicy
from app.modules.execution.infrastructure.browser_driver import SimulatedBrowserDriver
from app.modules.execution.infrastructure.desktop_driver import LocalSandboxDesktopDriver
from app.modules.execution.infrastructure.repositories import SqlAlchemyExecutionRunRepository
from app.modules.execution.presentation.dependencies import build_sandbox_policy
from app.modules.agents.application.document_agent import DocumentAgentService
from app.modules.knowledge.application.commands import SearchQuery
from app.modules.knowledge.application.indexing import KnowledgeIndexService
from app.modules.knowledge.infrastructure.chunk_repository import SqlAlchemyChunkRepository
from app.modules.knowledge.infrastructure.chunker import StructureAwareChunker
from app.modules.knowledge.infrastructure.embedding import HashingEmbeddingProvider
from app.modules.knowledge.infrastructure.source import RepositoryDocumentSource
from app.modules.knowledge.infrastructure.vector_store import QdrantVectorStore
from app.modules.memory.application.long_term_memory import LongTermMemoryService
from app.modules.memory.application.memory_agent import MemoryAgentService
from app.modules.memory.application.session_memory import SessionMemoryService
from app.modules.memory.infrastructure.memory_vector import QdrantMemoryVectorIndex
from app.modules.memory.infrastructure.repositories import (
    SqlAlchemyMemoryItemRepository,
    SqlAlchemyMemoryReferenceRepository,
)
from app.modules.memory.infrastructure.session_store import RedisSessionMemoryStore
from app.modules.qa.application.qa_agent import QaAgentService
from app.modules.workflows.domain.executor import StepExecutor, StepRequest, StepResult
from app.modules.workflows.infrastructure.llm_executor import LlmStepExecutor
from app.shared.llm.provider import LLMProvider

# agent_type -> bound handler method name
_DISPATCH: dict[str, str] = {
    "DocumentAgent": "_run_document",
    "KnowledgeAgent": "_run_knowledge",
    "AnalysisAgent": "_run_analysis",
    "QAAgent": "_run_qa",
    "ReportAgent": "_run_report",
    "MemoryAgent": "_run_memory",
    "ExecutionAgent": "_run_execution",
}


class AgentStepExecutor(StepExecutor):
    def __init__(
        self,
        *,
        session: AsyncSession,
        llm: LLMProvider,
        fallback: StepExecutor | None = None,
        sandbox_policy: SandboxPolicy | None = None,
    ) -> None:
        self._session = session
        self._llm = llm
        self._fallback = fallback or LlmStepExecutor(llm)
        self._sandbox_policy = sandbox_policy or build_sandbox_policy()

    async def execute(self, step: StepRequest) -> StepResult:
        method = _DISPATCH.get(step.agent_type)
        if method is None:  # CriticAgent / ResearchAgent: no dedicated service yet
            return await self._fallback.execute(step)
        result = await getattr(self, method)(step)
        if result is None:  # required input unavailable -> degrade (FH-001)
            return await self._fallback.execute(step)
        return result

    # --- agent handlers ------------------------------------------------- #

    async def _run_document(self, step: StepRequest) -> StepResult | None:
        document_id = self._opt_uuid(step.context, "document_id")
        if document_id is None:
            return None
        service = DocumentAgentService(SqlAlchemyDocumentRepository(self._session))
        res = await service.analyze(document_id)
        text = res.summary or f"Classified document as '{res.classification}'."
        return self._ok(
            "DocumentAgent",
            text,
            {
                "document_id": str(res.document_id),
                "classification": res.classification,
                "categories": res.categories,
                "language": res.language,
            },
        )

    async def _run_knowledge(self, step: StepRequest) -> StepResult:
        query = (step.objective or step.request).strip()
        hits = await self._knowledge_service().search(
            SearchQuery(query=query, document_id=self._opt_uuid(step.context, "document_id"))
        )
        text = (
            f"Retrieved {len(hits)} relevant passage(s)."
            if hits
            else "No indexed passages matched the query."
        )
        return self._ok(
            "KnowledgeAgent",
            text,
            {"count": len(hits), "chunk_ids": [str(h.chunk_id) for h in hits]},
        )

    async def _run_analysis(self, step: StepRequest) -> StepResult | None:
        document_ids = self._opt_uuid_list(step.context, "document_ids")
        if not document_ids:
            single = self._opt_uuid(step.context, "document_id")
            document_ids = [single] if single else []
        if not document_ids:
            return None
        service = AnalysisAgentService(
            documents=SqlAlchemyDocumentRepository(self._session),
            jobs=SqlAlchemyAnalysisJobRepository(self._session),
        )
        res = await service.analyze_documents(document_ids)
        return self._ok(
            "AnalysisAgent",
            res.summary,
            {
                # consumed by a downstream ReportAgent step (EX-003)
                "analysis_job_id": str(res.job_id),
                "statistics": res.statistics,
                "findings": res.findings,
                "recommendations": res.recommendations,
            },
        )

    async def _run_qa(self, step: StepRequest) -> StepResult:
        service = QaAgentService(retriever=self._knowledge_service(), llm=self._llm)
        question = (step.request or step.objective).strip()
        answer = await service.ask(
            question, document_id=self._opt_uuid(step.context, "document_id")
        )
        return self._ok(
            "QAAgent",
            answer.answer,
            {
                "grounded": answer.grounded,
                "llm_used": answer.llm_used,
                "citations": [c.snippet for c in answer.citations],
            },
        )

    async def _run_report(self, step: StepRequest) -> StepResult | None:
        analysis_job_id = self._find_uuid(step.context, "analysis_job_id")
        if analysis_job_id is None:
            return None
        service = self._report_service()
        report_format = str(step.context.get("report_format") or "markdown")
        res = await service.generate_from_analysis(
            analysis_job_id, report_format=report_format
        )
        return self._ok(
            "ReportAgent",
            res.content,
            {"report_id": str(res.report_id), "format": res.format},
        )

    async def _run_memory(self, step: StepRequest) -> StepResult:
        service = MemoryAgentService(
            session=SessionMemoryService(RedisSessionMemoryStore(get_redis())),
            long_term=LongTermMemoryService(
                items=SqlAlchemyMemoryItemRepository(self._session),
                references=SqlAlchemyMemoryReferenceRepository(self._session),
                embedder=HashingEmbeddingProvider(),
                vectors=QdrantMemoryVectorIndex(),
            ),
            knowledge=self._knowledge_service(),
        )
        query = (step.request or step.objective).strip()
        ctx = await service.assemble_context(
            query,
            session_id=_opt_str(step.context, "session_id"),
            working=_opt_str(step.context, "working"),
        )
        return self._ok(
            "MemoryAgent",
            ctx.text or "(no prior memory available)",
            {"session_id": ctx.session_id, "knowledge_hits": len(ctx.knowledge)},
        )

    async def _run_execution(self, step: StepRequest) -> StepResult | None:
        raw = step.context.get("actions")
        if not isinstance(raw, list) or not raw:
            # No concrete actions: never fabricate side effects — describe instead.
            return None
        actions = [
            Action(
                kind=str(item.get("kind", "")),
                type=str(item.get("type", "")),
                params=item.get("params") if isinstance(item.get("params"), dict) else {},
            )
            for item in raw
            if isinstance(item, dict)
        ]
        if not actions:
            return None
        policy = self._sandbox_policy
        service = ExecutionAgentService(
            runs=SqlAlchemyExecutionRunRepository(self._session),
            sandbox=SafeExecutionSandbox(policy),
            browser=SimulatedBrowserDriver(),
            desktop=LocalSandboxDesktopDriver(policy),
        )
        # The engine's Human Approval gate has already cleared this step
        # (ExecutionAgent.requires_approval); the sandbox still enforces SB-*.
        report = await service.run_plan(actions, approved=True)
        return self._ok(
            "ExecutionAgent",
            f"Execution {report.status}: ran {len(report.outcomes)} action(s).",
            {
                "run_id": str(report.run_id),
                "status": report.status,
                "outcomes": [o.status for o in report.outcomes],
            },
        )

    # --- helpers -------------------------------------------------------- #

    def _knowledge_service(self) -> KnowledgeIndexService:
        return KnowledgeIndexService(
            source=RepositoryDocumentSource(SqlAlchemyDocumentRepository(self._session)),
            chunker=StructureAwareChunker(),
            chunks=SqlAlchemyChunkRepository(self._session),
            embedder=HashingEmbeddingProvider(),
            vector_store=QdrantVectorStore(),
        )

    def _report_service(self):
        from app.modules.reports.application.report_agent import ReportAgentService
        from app.modules.reports.infrastructure.repositories import SqlAlchemyReportRepository

        return ReportAgentService(
            jobs=SqlAlchemyAnalysisJobRepository(self._session),
            reports=SqlAlchemyReportRepository(self._session),
        )

    @staticmethod
    def _ok(agent: str, result: str, extra: dict) -> StepResult:
        # "result" is the text downstream steps and the engine context read.
        return StepResult(output={"agent": agent, "result": result, **extra})

    @staticmethod
    def _opt_uuid(context: dict, key: str) -> uuid.UUID | None:
        return _to_uuid(context.get(key))

    @staticmethod
    def _opt_uuid_list(context: dict, key: str) -> list[uuid.UUID]:
        raw = context.get(key)
        if not isinstance(raw, (list, tuple)):
            return []
        parsed = [_to_uuid(v) for v in raw]
        return [u for u in parsed if u is not None]

    @staticmethod
    def _find_uuid(context: dict, key: str) -> uuid.UUID | None:
        """Find ``key`` directly in context, else in any prior step's output."""
        direct = _to_uuid(context.get(key))
        if direct is not None:
            return direct
        found: uuid.UUID | None = None
        for value in context.values():
            if isinstance(value, dict) and key in value:
                candidate = _to_uuid(value.get(key))
                if candidate is not None:
                    found = candidate  # keep the latest match
        return found


def _to_uuid(value) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return None
    return None


def _opt_str(context: dict, key: str) -> str | None:
    value = context.get(key)
    return value if isinstance(value, str) and value.strip() else None
