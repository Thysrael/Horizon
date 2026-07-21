"""Worker process entry point."""

from __future__ import annotations

import asyncio
import uuid

from aiogram import Bot

from src.infoservice.db.session import create_session_factory
from src.infoservice.db.heartbeats import touch_heartbeat
from src.infoservice.delivery.telegram import TelegramDelivery, TelegramReportRenderer
from src.infoservice.execution.horizon import HorizonReportExecutor
from src.infoservice.security.credentials import CredentialCipher
from src.infoservice.settings import Settings

from .service import ExecutionContext, ExecutionService, SqlExecutionStore

__all__ = ("ExecutionContext", "ExecutionService", "run_worker")


async def run_worker(settings: Settings, bot: Bot, stop_event: asyncio.Event) -> None:
    factory = create_session_factory(settings.database_url)
    service = ExecutionService(
        store=SqlExecutionStore(factory), executor=HorizonReportExecutor(settings),
        delivery=TelegramDelivery(bot), renderer=TelegramReportRenderer(),
        cipher=CredentialCipher(settings.app_encryption_key.get_secret_value()), worker_id=f"worker-{uuid.uuid4().hex[:12]}",
        semaphore=asyncio.Semaphore(settings.worker_concurrency),
    )
    active: set[asyncio.Task[None]] = set()

    async def consume() -> None:
        while not stop_event.is_set():
            if not await service.run_once():
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=1)
                except TimeoutError:
                    pass

    async def heartbeat() -> None:
        while not stop_event.is_set():
            await touch_heartbeat(factory, "worker")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except TimeoutError:
                pass

    for _ in range(settings.worker_concurrency):
        task = asyncio.create_task(consume())
        active.add(task)
    heartbeat_task = asyncio.create_task(heartbeat())
    try:
        await stop_event.wait()
        _, pending = await asyncio.wait(active, timeout=30)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)


def main() -> None:
    async def run() -> None:
        settings = Settings()
        bot = Bot(settings.telegram_bot_token.get_secret_value())
        await run_worker(settings, bot, asyncio.Event())
    asyncio.run(run())
