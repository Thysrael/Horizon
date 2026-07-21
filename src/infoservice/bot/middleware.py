from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infoservice.bot.messages_ru import GROUP_PRIVATE_REDIRECT
from src.infoservice.db.repositories.users import UserRepository


class PrivateUserMiddleware(BaseMiddleware):
    """Reject non-private events and provide one transaction-scoped DB session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        message = event if isinstance(event, Message) else event.message if isinstance(event, CallbackQuery) else None
        chat = message.chat if message is not None else None
        actor = event.from_user if isinstance(event, (Message, CallbackQuery)) else None
        if chat is None or actor is None:
            return await handler(event, data)
        if chat.type != ChatType.PRIVATE:
            if isinstance(event, CallbackQuery):
                await event.answer(GROUP_PRIVATE_REDIRECT, show_alert=True)
            else:
                await message.answer(GROUP_PRIVATE_REDIRECT)
            return None

        async with self._session_factory() as session:
            user = await UserRepository(session).get_or_create(actor.id, chat.id)
            data["session"] = session
            data["user"] = user
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
