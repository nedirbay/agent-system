from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.application.services import UserService
from app.modules.auth.infrastructure.repositories import SqlAlchemyUserRepository


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(SqlAlchemyUserRepository(session))
