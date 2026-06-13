from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.modules.agents.application.commands import CreateAgentCommand
from app.modules.agents.application.document_agent import DocumentAgentService
from app.modules.agents.application.orchestrator import OrchestratorService
from app.modules.agents.application.services import AgentService
from app.modules.agents.domain.registry import AGENT_REGISTRY
from app.modules.agents.presentation.dependencies import (
    get_agent_service,
    get_document_agent_service,
    get_orchestrator_service,
)
from app.modules.agents.presentation.schemas import (
    AgentCreate,
    AgentRead,
    AgentSpecRead,
    DocumentAgentAnalysisRead,
    PlannedStepRead,
    PlanRead,
    PlanRequest,
)

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/registry", response_model=list[AgentSpecRead])
async def list_agent_registry() -> list[AgentSpecRead]:
    """The catalogue of agent types the Orchestrator can plan and route to."""
    return [
        AgentSpecRead(
            type=s.type,
            description=s.description,
            task_class=s.task_class,
            tier=s.tier,
            capabilities=list(s.capabilities),
            requires_approval=s.requires_approval,
        )
        for s in AGENT_REGISTRY.values()
    ]


@router.post("/orchestrator/plan", response_model=PlanRead)
async def orchestrator_plan(
    payload: PlanRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> PlanRead:
    """Decompose a request into a routed, ordered agent plan (Tasks 11–12)."""
    plan = await service.plan(payload.request, context=payload.context)
    return PlanRead(
        request=plan.request,
        summary=plan.summary,
        fallback=plan.fallback,
        steps=[
            PlannedStepRead(
                step_order=s.step_order,
                agent_type=s.agent_type,
                objective=s.objective,
                tier=s.tier,
                model=s.model,
                requires_approval=s.requires_approval,
            )
            for s in plan.steps
        ],
    )


@router.post(
    "/document-agent/documents/{document_id}/analyze",
    response_model=DocumentAgentAnalysisRead,
)
async def analyze_document_with_agent(
    document_id: uuid.UUID,
    service: DocumentAgentService = Depends(get_document_agent_service),
) -> DocumentAgentAnalysisRead:
    """Analyze a parsed document with the specialized Document Agent."""
    result = await service.analyze(document_id)
    return DocumentAgentAnalysisRead(
        document_id=result.document_id,
        file_name=result.file_name,
        summary=result.summary,
        language=result.language,
        categories=result.categories,
        classification=result.classification,
        metadata=result.metadata,
    )


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
