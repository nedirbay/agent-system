from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.agents.domain.entities import Agent


class AgentRepository(AbstractRepository[Agent], ABC):
    """Persistence port for Agent aggregates."""
