"""In-process LLM step executor (Roadmap Task 13, MVP).

Runs each workflow step by prompting the LLM in the role of the target agent,
grounded in the original request and the accumulated workflow context. The
specialized agents (Faza 5) will replace this behind the same `StepExecutor`
port; the engine does not change.
"""
from __future__ import annotations

import json

from app.modules.agents.domain.registry import get_spec
from app.modules.workflows.domain.executor import StepExecutor, StepRequest, StepResult
from app.shared.llm.provider import ChatMessage, LLMProvider

_SYSTEM = (
    "You are the {agent_type} in a multi-agent platform. {description}\n"
    "Carry out ONLY this step's objective. Be concise and concrete. Use the "
    "provided context from earlier steps; do not invent facts. If the context "
    "is insufficient, say so explicitly."
)


class LlmStepExecutor(StepExecutor):
    def __init__(self, llm: LLMProvider, *, max_tokens: int = 400) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

    async def execute(self, step: StepRequest) -> StepResult:
        spec = get_spec(step.agent_type)
        description = spec.description if spec else ""
        system = _SYSTEM.format(agent_type=step.agent_type, description=description)

        context_blob = self._render_context(step.context)
        user = (
            f"Original request:\n{step.request}\n\n"
            f"Context so far:\n{context_blob or '(empty)'}\n\n"
            f"Your step objective:\n{step.objective}"
        )
        result = await self._llm.complete(
            [ChatMessage("system", system), ChatMessage("user", user)],
            model=step.model,
            temperature=0.2,
            max_tokens=self._max_tokens,
        )
        return StepResult(
            output={
                "result": result.text.strip(),
                "model": result.model,
                "tokens": {
                    "prompt": result.prompt_tokens,
                    "completion": result.completion_tokens,
                },
            }
        )

    @staticmethod
    def _render_context(context: dict) -> str:
        # Show prior step outputs compactly (their "result" text where present).
        lines: list[str] = []
        for key, value in context.items():
            if isinstance(value, dict) and "result" in value:
                lines.append(f"[{key}] {value['result']}")
            else:
                lines.append(f"[{key}] {json.dumps(value, ensure_ascii=False)[:500]}")
        return "\n".join(lines)
