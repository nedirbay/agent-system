"""Registry-driven agent router (Roadmap Task 12).

Validates every planned step against the agent registry and stamps it with the
model tier + concrete model id (MR-002, data-driven from settings) and whether
it needs human approval (HA-003).
"""
from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.agents.domain.planning import Plan
from app.modules.agents.domain.registry import (
    TIER_GENERAL,
    TIER_LIGHT,
    TIER_REASONING,
    get_spec,
)
from app.modules.agents.domain.routing import AgentRouter


class UnknownAgentError(AppError):
    status_code = 422
    code = "unknown_agent"


class RegistryAgentRouter(AgentRouter):
    def __init__(self) -> None:
        settings = get_settings()
        self._tier_models = {
            TIER_REASONING: settings.llm_model_reasoning,
            TIER_GENERAL: settings.llm_model_general,
            TIER_LIGHT: settings.llm_model_light,
        }

    def route(self, plan: Plan) -> Plan:
        for step in plan.steps:
            spec = get_spec(step.agent_type)
            if spec is None:
                raise UnknownAgentError(f"Unknown agent type: {step.agent_type}")
            step.tier = spec.tier
            step.model = self._tier_models.get(spec.tier, self._tier_models[TIER_GENERAL])
            step.requires_approval = spec.requires_approval
        return plan

    def resolve_model(self, agent_type: str) -> str:
        spec = get_spec(agent_type)
        if spec is None:
            raise UnknownAgentError(f"Unknown agent type: {agent_type}")
        return self._tier_models.get(spec.tier, self._tier_models[TIER_GENERAL])
