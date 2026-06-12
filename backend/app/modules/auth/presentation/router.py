from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.application.commands import (
    AuthenticateCommand,
    RegisterUserCommand,
)
from app.modules.auth.application.services import UserService
from app.modules.auth.presentation.dependencies import get_user_service
from app.modules.auth.presentation.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


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
) -> TokenResponse:
    token = await service.authenticate(AuthenticateCommand(**payload.model_dump()))
    return TokenResponse(access_token=token)


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
