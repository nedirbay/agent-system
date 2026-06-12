from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.agents.application.commands import CreateAgentCommand
from app.modules.agents.application.services import AgentService
from app.modules.agents.presentation.dependencies import get_agent_service
from app.modules.agents.presentation.schemas import AgentCreate, AgentRead

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=AgentRead, status_code=201)
async def create_agent(
    payload: AgentCreate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    command = CreateAgentCommand(**payload.model_dump())
    entity = await service.create(command)
    return AgentRead.model_validate(entity)


@router.get("", response_model=list[AgentRead])
async def list_agent(
    limit: int = 100,
    offset: int = 0,
    service: AgentService = Depends(get_agent_service),
) -> list[AgentRead]:
    items = await service.list(limit=limit, offset=offset)
    return [AgentRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=AgentRead)
async def get_agent(
    item_id: uuid.UUID,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    entity = await service.get(item_id)
    return AgentRead.model_validate(entity)
