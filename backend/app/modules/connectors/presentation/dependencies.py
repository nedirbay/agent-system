from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.connectors.application.services import ConnectorService
from app.modules.connectors.infrastructure.repositories import (
    SqlAlchemyConnectorConnectionRepository,
)


def get_connector_service(
    session: AsyncSession = Depends(get_session),
) -> ConnectorService:
    return ConnectorService(SqlAlchemyConnectorConnectionRepository(session))
