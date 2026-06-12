from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.analysis.domain.entities import AnalysisJob


class AnalysisJobRepository(AbstractRepository[AnalysisJob], ABC):
    """Persistence port for AnalysisJob aggregates."""
