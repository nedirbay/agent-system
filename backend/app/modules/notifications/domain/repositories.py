from __future__ import annotations

from abc import ABC

from app.shared.domain.repository import AbstractRepository
from app.modules.notifications.domain.entities import Notification


class NotificationRepository(AbstractRepository[Notification], ABC):
    """Persistence port for Notification aggregates."""
