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
        users = (await self.session.execute(stmt)).scalars().all()
        if users:
            if len(users) != 1 or users[0].telegram_user_id != telegram_user_id or users[0].chat_id != chat_id:
                raise Conflict("Этот чат уже привязан к другому пользователю")
            return users[0]

        try:
            async with self.session.begin_nested():
                user = User(telegram_user_id=telegram_user_id, chat_id=chat_id, timezone=timezone)
                self.session.add(user)
                await self.session.flush()
        except IntegrityError:
            users = (await self.session.execute(stmt)).scalars().all()
            if len(users) != 1 or users[0].telegram_user_id != telegram_user_id or users[0].chat_id != chat_id:
                raise Conflict("Этот чат уже привязан к другому пользователю")
            user = users[0]
        return user
