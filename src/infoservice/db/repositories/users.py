from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.db.models import User
from src.infoservice.errors import Conflict


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, telegram_user_id: int, chat_id: int, *, timezone: str = "UTC") -> User:
        stmt = select(User).where(or_(User.telegram_user_id == telegram_user_id, User.chat_id == chat_id))
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if user is not None:
            if user.telegram_user_id != telegram_user_id or user.chat_id != chat_id:
                raise Conflict("Этот чат уже привязан к другому пользователю")
            return user

        try:
            async with self.session.begin_nested():
                user = User(telegram_user_id=telegram_user_id, chat_id=chat_id, timezone=timezone)
                self.session.add(user)
                await self.session.flush()
        except IntegrityError:
            user = (await self.session.execute(stmt)).scalar_one_or_none()
            if user is None or user.telegram_user_id != telegram_user_id or user.chat_id != chat_id:
                raise Conflict("Этот чат уже привязан к другому пользователю")
        return user
