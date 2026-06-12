from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.reports.domain.entities import Report


class ReportRepository(AbstractRepository[Report], ABC):
    """Persistence port for Report aggregates."""
