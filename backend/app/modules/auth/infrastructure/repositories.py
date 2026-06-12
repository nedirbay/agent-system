from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import User
from app.modules.auth.domain.repositories import UserRepository
from app.modules.auth.infrastructure.models import UserModel


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        created_at=model.created_at,
        username=model.username,
        email=model.email,
        full_name=model.full_name,
        password_hash=model.password_hash,
        status=model.status,
    )


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy adapter implementing the User port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: User) -> User:
        model = UserModel(
            id=entity.id,
            created_at=entity.created_at,
            username=entity.username,
            email=entity.email,
            full_name=entity.full_name,
            password_hash=entity.password_hash,
            status=entity.status,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get(self, entity_id: uuid.UUID) -> User | None:
        model = await self._session.get(UserModel, entity_id)
        return _to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        result = await self._session.execute(
            select(UserModel).limit(limit).offset(offset)
        )
        return [_to_entity(m) for m in result.scalars().all()]
