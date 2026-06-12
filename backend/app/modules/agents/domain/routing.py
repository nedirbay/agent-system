"""Agent routing domain (Roadmap Task 12 / AG-001).

Routing maps each planned step to a concrete agent + model tier and validates
that the chosen agent exists in the registry. Mapping is data-driven (MR-002).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.agents.domain.planning import Plan


class AgentRouter(ABC):
    @abstractmethod
    def route(self, plan: Plan) -> Plan:
        """Assign tier/model/approval to every step; raise on unknown agents."""

    @abstractmethod
    def resolve_model(self, agent_type: str) -> str:
        """Return the concrete model id serving an agent type."""
