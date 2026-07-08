"""Tests for AgentStepExecutor — the brain→real-agent dispatch (Task 13 / EX-001).

These exercise the executor's contract without a live DB: dispatch routing,
graceful fallback to the LLM role-play executor (FH-001), and the context-based
input resolution that lets one step's output feed the next (EX-003).
"""
from __future__ import annotations

import uuid

import pytest

from app.modules.workflows.domain.executor import StepExecutor, StepRequest, StepResult
from app.modules.workflows.infrastructure.agent_executor import AgentStepExecutor


class _RecordingFallback(StepExecutor):
    """Stands in for the LLM role-play executor; records that it was used."""

    def __init__(self) -> None:
        self.calls: list[StepRequest] = []

    async def execute(self, step: StepRequest) -> StepResult:
        self.calls.append(step)
        return StepResult(output={"agent": step.agent_type, "result": "fallback", "fallback": True})


class _StubExecutor(AgentStepExecutor):
    """AgentStepExecutor with real handlers stubbed so no DB/LLM is needed."""

    def __init__(self, fallback: StepExecutor, *, handler_returns: dict | None = None) -> None:
        super().__init__(session=object(), llm=object(), fallback=fallback)
        self._returns = handler_returns or {}
        self.dispatched: list[str] = []

    async def _stub(self, step: StepRequest):  # noqa: D401 - test helper
        self.dispatched.append(step.agent_type)
        return self._returns.get(step.agent_type)

    # Override every real handler with the stub.
    _run_document = _stub
    _run_knowledge = _stub
    _run_analysis = _stub
    _run_qa = _stub
    _run_report = _stub
    _run_memory = _stub
    _run_execution = _stub


def _step(agent_type: str, *, objective: str = "do it", context: dict | None = None) -> StepRequest:
    return StepRequest(
        agent_type=agent_type,
        objective=objective,
        model="m",
        request="user request",
        context=context or {},
    )


# --- dispatch routing -------------------------------------------------- #


@pytest.mark.asyncio
async def test_known_agent_dispatches_to_real_handler() -> None:
    fallback = _RecordingFallback()
    executor = _StubExecutor(
        fallback,
        handler_returns={"QAAgent": StepResult(output={"result": "real answer"})},
    )

    result = await executor.execute(_step("QAAgent"))

    assert executor.dispatched == ["QAAgent"]
    assert result.output["result"] == "real answer"
    assert fallback.calls == []  # the real agent ran; no fallback


@pytest.mark.asyncio
async def test_unknown_agent_type_falls_back_to_llm_roleplay() -> None:
    fallback = _RecordingFallback()
    executor = _StubExecutor(fallback)

    result = await executor.execute(_step("CriticAgent"))

    assert executor.dispatched == []  # no real handler exists
    assert result.output["fallback"] is True
    assert [c.agent_type for c in fallback.calls] == ["CriticAgent"]


@pytest.mark.asyncio
async def test_missing_input_degrades_to_fallback() -> None:
    fallback = _RecordingFallback()
    # Handler returns None (e.g. DocumentAgent with no document_id in context).
    executor = _StubExecutor(fallback, handler_returns={"DocumentAgent": None})

    result = await executor.execute(_step("DocumentAgent"))

    assert executor.dispatched == ["DocumentAgent"]  # real handler tried first
    assert result.output["fallback"] is True  # then degraded
    assert [c.agent_type for c in fallback.calls] == ["DocumentAgent"]


# --- input resolution (EX-003 chaining) -------------------------------- #


def test_find_uuid_reads_a_prior_steps_output() -> None:
    job_id = uuid.uuid4()
    # Mimics the engine context after an AnalysisAgent step ran.
    context = {
        "user": "alice",
        "step1_AnalysisAgent": {"result": "analyzed", "analysis_job_id": str(job_id)},
    }
    assert AgentStepExecutor._find_uuid(context, "analysis_job_id") == job_id


def test_find_uuid_prefers_direct_context_key() -> None:
    direct = uuid.uuid4()
    nested = uuid.uuid4()
    context = {
        "analysis_job_id": str(direct),
        "step1_AnalysisAgent": {"analysis_job_id": str(nested)},
    }
    assert AgentStepExecutor._find_uuid(context, "analysis_job_id") == direct


def test_opt_uuid_list_parses_and_rejects_garbage() -> None:
    good = uuid.uuid4()
    context = {"document_ids": [str(good), "not-a-uuid", 123]}
    assert AgentStepExecutor._opt_uuid_list(context, "document_ids") == [good]


def test_opt_uuid_returns_none_for_missing_or_invalid() -> None:
    assert AgentStepExecutor._opt_uuid({}, "document_id") is None
    assert AgentStepExecutor._opt_uuid({"document_id": "nope"}, "document_id") is None
    real = uuid.uuid4()
    assert AgentStepExecutor._opt_uuid({"document_id": real}, "document_id") == real
