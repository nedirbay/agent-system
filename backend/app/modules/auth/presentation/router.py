from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, status

from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import UnauthorizedError
from app.modules.audit.application.services import AuditLogService
from app.modules.audit.presentation.dependencies import get_auditlog_service
from app.modules.auth.application.commands import (
    AuthenticateCommand,
    RegisterUserCommand,
)
from app.modules.auth.application.services import UserService
from app.modules.auth.presentation.dependencies import get_user_service
from app.modules.auth.presentation.schemas import (
    CurrentUserRead,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _correlation_id() -> str | None:
    return structlog.contextvars.get_contextvars().get("correlation_id")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.register(RegisterUserCommand(**payload.model_dump()))
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    service: UserService = Depends(get_user_service),
    audit: AuditLogService = Depends(get_auditlog_service),
) -> TokenResponse:
    cid = _correlation_id()
    try:
        token = await service.authenticate(AuthenticateCommand(**payload.model_dump()))
    except UnauthorizedError:
        # Security event: failed login (AUD-002).
        await audit.record_security_event(
            "LoginFailed",
            details={"username": payload.username},
            correlation_id=cid,
        )
        raise
    await audit.record_security_event(
        "LoginSuccess",
        details={"username": payload.username},
        correlation_id=cid,
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=CurrentUserRead)
async def me(current: CurrentUser = Depends(get_current_user)) -> CurrentUserRead:
    """Return the authenticated identity — requires a valid bearer token (Task 30)."""
    return CurrentUserRead(id=current.id, username=current.username)


@router.get("/users", response_model=list[UserRead])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    items = await service.list(limit=limit, offset=offset)
    return [UserRead.model_validate(i) for i in items]


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.get(user_id)
    return UserRead.model_validate(user)
