from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.execution.domain.entities import ExecutionRun


class ExecutionRunRepository(AbstractRepository[ExecutionRun], ABC):
    """Persistence port for ExecutionRun aggregates."""
