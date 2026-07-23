"""Telegram bot application factory and polling entry point."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infoservice.bot.commands import configure_bot_commands
from src.infoservice.bot.handlers.credentials import router as credentials_router
from src.infoservice.bot.handlers.navigation import router as navigation_router
from src.infoservice.bot.handlers.start import router as start_router
from src.infoservice.bot.handlers.reports import router as reports_router
from src.infoservice.bot.handlers.rules import router as rules_router
from src.infoservice.bot.handlers.schedules import router as schedules_router
from src.infoservice.bot.handlers.source_wizard import (
    router as source_wizard_router,
)
from src.infoservice.bot.handlers.sources import router as sources_router
from src.infoservice.bot.middleware import PrivateUserMiddleware
from src.infoservice.db.session import create_session_factory
from src.infoservice.db.heartbeats import touch_heartbeat
from src.infoservice.llm.deepseek import DeepSeekVerifier
from src.infoservice.security.credentials import CredentialCipher
from src.infoservice.settings import Settings


def create_dispatcher(settings: Settings, session_factory: async_sessionmaker[AsyncSession]) -> Dispatcher:
    """Build the one dispatcher used by the bot process."""
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.workflow_data.update(
        cipher=CredentialCipher(settings.app_encryption_key.get_secret_value()),
        verifier=DeepSeekVerifier(),
        settings=settings,
    )
    dispatcher.message.outer_middleware(PrivateUserMiddleware(session_factory))
    dispatcher.callback_query.outer_middleware(PrivateUserMiddleware(session_factory))
    dispatcher.include_routers(
        navigation_router,
        start_router,
        credentials_router,
        reports_router,
        rules_router,
        schedules_router,
        sources_router,
        source_wizard_router,
    )
    return dispatcher


async def run() -> None:
    settings = Settings()
    session_factory = create_session_factory(settings.database_url)
    dispatcher = create_dispatcher(settings, session_factory)
    bot = Bot(settings.telegram_bot_token.get_secret_value())
    await configure_bot_commands(bot)
    stop_event = asyncio.Event()

    async def heartbeat() -> None:
        while not stop_event.is_set():
            await touch_heartbeat(session_factory, "bot")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except TimeoutError:
                pass

    heartbeat_task = asyncio.create_task(heartbeat())
    try:
        await dispatcher.start_polling(bot, tasks_concurrency_limit=32)
    finally:
        stop_event.set()
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)


def main() -> None:
    asyncio.run(run())
