"""Telegram bot application factory and polling entry point."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infoservice.bot.handlers.credentials import router as credentials_router
from src.infoservice.bot.handlers.start import router as start_router
from src.infoservice.bot.handlers.reports import router as reports_router
from src.infoservice.bot.handlers.rules import router as rules_router
from src.infoservice.bot.handlers.schedules import router as schedules_router
from src.infoservice.bot.middleware import PrivateUserMiddleware
from src.infoservice.db.session import create_session_factory
from src.infoservice.llm.deepseek import DeepSeekVerifier
from src.infoservice.security.credentials import CredentialCipher
from src.infoservice.settings import Settings


def create_dispatcher(settings: Settings, session_factory: async_sessionmaker[AsyncSession]) -> Dispatcher:
    """Build the one dispatcher used by the bot process."""
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.workflow_data.update(
        cipher=CredentialCipher(settings.app_encryption_key.get_secret_value()),
        verifier=DeepSeekVerifier(),
    )
    dispatcher.message.outer_middleware(PrivateUserMiddleware(session_factory))
    dispatcher.callback_query.outer_middleware(PrivateUserMiddleware(session_factory))
    dispatcher.include_routers(start_router, credentials_router, reports_router, rules_router, schedules_router)
    return dispatcher


async def run() -> None:
    settings = Settings()
    dispatcher = create_dispatcher(settings, create_session_factory(settings.database_url))
    bot = Bot(settings.telegram_bot_token.get_secret_value())
    await dispatcher.start_polling(bot, tasks_concurrency_limit=32)


def main() -> None:
    asyncio.run(run())
