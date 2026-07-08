from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status

from app.core.auth import CurrentUser, get_current_user
from app.modules.connectors.application.commands import AddConnectorCommand
from app.modules.connectors.application.services import ConnectorService
from app.modules.connectors.presentation.dependencies import get_connector_service
from app.modules.connectors.presentation.schemas import (
    AddConnectorRequest,
    ConnectorConnectionRead,
    ConnectorSpecRead,
)

router = APIRouter(prefix="/connectors", tags=["Connectors"])


def _user_uuid(current: CurrentUser) -> uuid.UUID | None:
    """The JWT subject is the user's UUID; tolerate non-UUID subjects."""
    try:
        return uuid.UUID(current.id)
    except (ValueError, TypeError):
        return None


@router.get("/catalog", response_model=list[ConnectorSpecRead])
async def list_catalog(
    service: ConnectorService = Depends(get_connector_service),
) -> list[ConnectorSpecRead]:
    """The catalogue of external systems a user can connect."""
    return [ConnectorSpecRead.from_spec(s) for s in service.list_catalog()]


@router.get("", response_model=list[ConnectorConnectionRead])
async def list_connections(
    limit: int = 100,
    offset: int = 0,
    current: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> list[ConnectorConnectionRead]:
    items = await service.list_connections(
        _user_uuid(current), limit=limit, offset=offset
    )
    return [ConnectorConnectionRead.from_entity(i) for i in items]


@router.post("", response_model=ConnectorConnectionRead, status_code=201)
async def add_connection(
    payload: AddConnectorRequest,
    current: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorConnectionRead:
    command = AddConnectorCommand(
        connector_type=payload.connector_type,
        user_id=_user_uuid(current),
        label=payload.label,
        values=payload.values,
    )
    entity = await service.add(command)
    return ConnectorConnectionRead.from_entity(entity)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    service: ConnectorService = Depends(get_connector_service),
) -> Response:
    await service.delete(_user_uuid(current), connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
