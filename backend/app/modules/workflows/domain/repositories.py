from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.workflows.domain.entities import Workflow


class WorkflowRepository(AbstractRepository[Workflow], ABC):
    """Persistence port for Workflow aggregates."""
