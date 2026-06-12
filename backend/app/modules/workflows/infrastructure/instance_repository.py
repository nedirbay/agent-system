from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflows.domain.instance import (
    WorkflowInstance,
    WorkflowInstanceRepository,
    WorkflowStep,
)
from app.modules.workflows.infrastructure.instance_models import (
    WorkflowInstanceModel,
    WorkflowStepModel,
)


def _step_to_entity(m: WorkflowStepModel) -> WorkflowStep:
    return WorkflowStep(
        id=m.id,
        created_at=m.created_at,
        instance_id=m.instance_id,
        step_order=m.step_order,
        agent_type=m.agent_type,
        objective=m.objective or "",
        tier=m.tier,
        model=m.model,
        requires_approval=m.requires_approval,
        status=m.status,
        attempts=m.attempts,
        output=m.output,
        error=m.error,
    )


def _instance_to_entity(
    m: WorkflowInstanceModel, steps: list[WorkflowStepModel]
) -> WorkflowInstance:
    return WorkflowInstance(
        id=m.id,
        created_at=m.created_at,
        task_id=m.task_id,
        request=m.request,
        summary=m.summary or "",
        status=m.status,
        current_step=m.current_step,
        context=m.context or {},
        fallback=m.fallback,
        steps=[_step_to_entity(s) for s in sorted(steps, key=lambda x: x.step_order)],
    )


class SqlAlchemyWorkflowInstanceRepository(WorkflowInstanceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, instance: WorkflowInstance) -> WorkflowInstance:
        model = WorkflowInstanceModel(
            id=instance.id,
            created_at=instance.created_at,
            task_id=instance.task_id,
            request=instance.request,
            summary=instance.summary,
            status=instance.status,
            current_step=instance.current_step,
            context=instance.context,
            fallback=instance.fallback,
        )
        self._session.add(model)
        self._session.add_all(self._step_models(instance))
        await self._session.flush()
        return instance

    async def get(self, instance_id: uuid.UUID) -> WorkflowInstance | None:
        model = await self._session.get(WorkflowInstanceModel, instance_id)
        if model is None:
            return None
        steps = await self._load_steps(instance_id)
        return _instance_to_entity(model, steps)

    async def save(self, instance: WorkflowInstance) -> WorkflowInstance:
        model = await self._session.get(WorkflowInstanceModel, instance.id)
        if model is None:
            raise KeyError(instance.id)
        model.status = instance.status
        model.summary = instance.summary
        model.current_step = instance.current_step
        model.context = instance.context
        model.fallback = instance.fallback

        existing = {s.id: s for s in await self._load_steps(instance.id)}
        for step in instance.steps:
            sm = existing.get(step.id)
            if sm is None:
                self._session.add(self._step_model(step, instance.id))
            else:
                sm.status = step.status
                sm.attempts = step.attempts
                sm.tier = step.tier
                sm.model = step.model
                sm.requires_approval = step.requires_approval
                sm.output = step.output
                sm.error = step.error
        await self._session.flush()
        return instance

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[WorkflowInstance]:
        result = await self._session.execute(
            select(WorkflowInstanceModel)
            .order_by(WorkflowInstanceModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_instance_to_entity(m, []) for m in result.scalars().all()]

    async def _load_steps(self, instance_id: uuid.UUID) -> list[WorkflowStepModel]:
        result = await self._session.execute(
            select(WorkflowStepModel)
            .where(WorkflowStepModel.instance_id == instance_id)
            .order_by(WorkflowStepModel.step_order)
        )
        return list(result.scalars().all())

    def _step_models(self, instance: WorkflowInstance) -> list[WorkflowStepModel]:
        return [self._step_model(s, instance.id) for s in instance.steps]

    @staticmethod
    def _step_model(step: WorkflowStep, instance_id: uuid.UUID) -> WorkflowStepModel:
        return WorkflowStepModel(
            id=step.id,
            created_at=step.created_at,
            instance_id=instance_id,
            step_order=step.step_order,
            agent_type=step.agent_type,
            objective=step.objective,
            tier=step.tier,
            model=step.model,
            requires_approval=step.requires_approval,
            status=step.status,
            attempts=step.attempts,
            output=step.output,
            error=step.error,
        )
