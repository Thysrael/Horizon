"""The durable scheduler process for InfoService reports."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Awaitable, Callable, Protocol

from sqlalchemy import delete

from src.infoservice.db.models import ReportRun
from src.infoservice.db.heartbeats import touch_heartbeat
from src.infoservice.db.session import create_session_factory
from src.infoservice.settings import Settings

from .repository import RunRepository, SchedulerRepository

logger = logging.getLogger(__name__)


class SchedulerOperations(Protocol):
    async def enqueue_due(self, now: datetime, limit: int) -> list[object]: ...
    async def recover_stale(self, now: datetime, timeout: timedelta) -> int: ...


class SchedulerService:
    """Perform one short scheduling transaction per poll.

    The class is deliberately independent of process management, making the
    scheduling safety properties testable without a running worker process.
    """

    def __init__(
        self,
        *,
        repository: SchedulerOperations,
        retention: Callable[[], Awaitable[None]],
        stale_timeout: timedelta,
        poll_seconds: float = 30,
        enqueue_limit: int = 100,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.retention = retention
        self.stale_timeout = stale_timeout
        self.poll_seconds = poll_seconds
        self.enqueue_limit = enqueue_limit
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._last_retention_day = None

    async def tick(self) -> None:
        now = self._now()
        enqueued = await self.repository.enqueue_due(now, self.enqueue_limit)
        recovered = await self.repository.recover_stale(now, self.stale_timeout)
        if self._last_retention_day != now.date():
            await self.retention()
            self._last_retention_day = now.date()
        logger.info("scheduler_tick", extra={"enqueued": len(enqueued or []), "recovered": recovered})

    async def run(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await self.tick()
            if stop_event.is_set():
                break
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.poll_seconds)
            except TimeoutError:
                pass


async def run_scheduler(settings: Settings, stop_event: asyncio.Event) -> None:
    factory = create_session_factory(settings.database_url)
    scheduler = SchedulerRepository(factory)
    runs = RunRepository(factory)

    async def retention() -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.run_retention_days)
        async with factory.begin() as session:
            await session.execute(delete(ReportRun).where(ReportRun.finished_at.is_not(None), ReportRun.finished_at < cutoff))

    service = SchedulerService(
        repository=SimpleNamespace(enqueue_due=scheduler.enqueue_due, recover_stale=runs.recover_stale),
        retention=retention,
        stale_timeout=timedelta(minutes=settings.stale_run_minutes),
        poll_seconds=settings.scheduler_poll_seconds,
    )
    async def heartbeat() -> None:
        while not stop_event.is_set():
            await touch_heartbeat(factory, "scheduler")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except TimeoutError:
                pass

    heartbeat_task = asyncio.create_task(heartbeat())
    try:
        await service.run(stop_event)
    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)


def main() -> None:
    asyncio.run(run_scheduler(Settings(), asyncio.Event()))
