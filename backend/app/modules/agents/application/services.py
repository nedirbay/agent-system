from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.agents.domain.entities import Agent
from app.modules.agents.domain.repositories import AgentRepository
from app.modules.agents.application.commands import CreateAgentCommand


class AgentService:
    """Application service orchestrating Agent use cases."""

    def __init__(self, repository: AgentRepository) -> None:
        self._repo = repository

    async def create(self, command: CreateAgentCommand) -> Agent:
        entity = Agent(name=command.name, type=command.type, description=command.description, is_active=command.is_active)
        return await self._repo.add(entity)

    async def get(self, entity_id: uuid.UUID) -> Agent:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("Agent not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Agent]:
        return await self._repo.list(limit=limit, offset=offset)
