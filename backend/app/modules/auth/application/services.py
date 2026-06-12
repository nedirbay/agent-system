from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.repositories import UserRepository
from app.modules.auth.application.commands import (
    AuthenticateCommand,
    RegisterUserCommand,
)


class UserService:
    """Application service orchestrating authentication use cases (FR-001)."""

    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    async def register(self, command: RegisterUserCommand) -> User:
        if await self._repo.get_by_username(command.username) is not None:
            raise ConflictError("A user with this username already exists")
        user = User(
            username=command.username,
            email=command.email,
            full_name=command.full_name,
            password_hash=hash_password(command.password),
            status="active",
        )
        return await self._repo.add(user)

    async def authenticate(self, command: AuthenticateCommand) -> str:
        user = await self._repo.get_by_username(command.username)
        if user is None or not verify_password(command.password, user.password_hash or ""):
            raise UnauthorizedError("Invalid credentials")
        return create_access_token(subject=str(user.id), extra={"username": user.username})

    async def get(self, entity_id: uuid.UUID) -> User:
        entity = await self._repo.get(entity_id)
        if entity is None:
            raise NotFoundError("User not found")
        return entity

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        return await self._repo.list(limit=limit, offset=offset)
