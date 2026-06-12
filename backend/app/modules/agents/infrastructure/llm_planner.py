"""LLM-backed task planner (Roadmap Task 11).

Uses the LLMProvider (Ollama / gemma4:31b-cloud) to decompose a request into an
ordered plan of agent steps, constrained to the agent registry via a JSON
schema (PR-003). If the LLM is unavailable or returns an unusable plan, it falls
back to a deterministic heuristic so the orchestrator still produces a plan
(FH-001 graceful degradation).
"""
from __future__ import annotations

from app.modules.agents.domain.planning import Plan, PlannedStep, TaskPlanner
from app.modules.agents.domain.registry import (
    AGENT_REGISTRY,
    PLANNABLE_AGENTS,
    registry_summary,
)
from app.shared.llm.provider import ChatMessage, LLMProvider

_SYSTEM = (
    "You are the Orchestrator Agent of a multi-agent platform. Decompose the "
    "user request into a short ordered plan of steps. Each step is handled by "
    "exactly ONE of these agents:\n{registry}\n\n"
    "Rules:\n"
    "- Use 2 to 6 steps, the minimum needed.\n"
    "- agent_type MUST be one of: {agents}.\n"
    "- Order steps so each builds on previous outputs (e.g. retrieve before answer).\n"
    "- 'objective' is a short imperative describing that step.\n"
    "Respond with JSON only."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "agent_type": {"type": "string", "enum": list(PLANNABLE_AGENTS)},
                    "objective": {"type": "string"},
                },
                "required": ["agent_type", "objective"],
            },
        },
    },
    "required": ["summary", "steps"],
}


class LlmTaskPlanner(TaskPlanner):
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def plan(self, request: str, *, context: str | None = None) -> Plan:
        system = _SYSTEM.format(
            registry=registry_summary(), agents=", ".join(PLANNABLE_AGENTS)
        )
        user = request if not context else f"Context:\n{context}\n\nRequest:\n{request}"
        try:
            data = await self._llm.complete_json(
                [ChatMessage("system", system), ChatMessage("user", user)],
                schema=_SCHEMA,
            )
            # The model may return {summary, steps} or a bare array (normalised
            # to {"items": [...]} by the provider).
            raw_steps = data.get("steps") or data.get("items")
            steps = self._coerce_steps(raw_steps)
            if steps:
                return Plan(
                    request=request,
                    summary=str(data.get("summary") or "").strip() or "Planned by orchestrator",
                    steps=steps,
                )
        except Exception:
            pass
        return self._fallback(request)

    def _coerce_steps(self, raw) -> list[PlannedStep]:
        steps: list[PlannedStep] = []
        if not isinstance(raw, list):
            return steps
        order = 1
        for item in raw:
            if not isinstance(item, dict):
                continue
            agent = str(item.get("agent_type", "")).strip()
            if agent not in AGENT_REGISTRY:
                continue  # drop hallucinated agent types
            steps.append(
                PlannedStep(
                    step_order=order,
                    agent_type=agent,
                    objective=str(item.get("objective", "")).strip() or agent,
                    inputs=item.get("inputs") if isinstance(item.get("inputs"), dict) else {},
                )
            )
            order += 1
        return steps

    def _fallback(self, request: str) -> Plan:
        """Deterministic default: retrieve → answer → validate."""
        lowered = request.lower()
        steps = [
            PlannedStep(1, "KnowledgeAgent", "Retrieve relevant context for the request"),
            PlannedStep(2, "QAAgent", "Answer the request grounded in retrieved context"),
            PlannedStep(3, "CriticAgent", "Validate the answer for grounding and consistency"),
        ]
        if any(w in lowered for w in ("report", "hasabat", "export", "pdf", "docx")):
            steps.insert(2, PlannedStep(3, "ReportAgent", "Produce the requested report"))
            for i, s in enumerate(steps, start=1):
                s.step_order = i
        return Plan(
            request=request,
            summary="Heuristic plan (LLM unavailable)",
            steps=steps,
            fallback=True,
        )
