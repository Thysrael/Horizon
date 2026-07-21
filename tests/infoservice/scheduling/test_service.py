from __future__ import annotations

import asyncio
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.infoservice.scheduling.service import SchedulerService


@pytest.mark.asyncio
async def test_scheduler_enqueues_recovers_and_runs_retention_once_per_day():
    repository = SimpleNamespace(enqueue_due=AsyncMock(return_value=[]), recover_stale=AsyncMock(return_value=0))
    retention = AsyncMock()
    service = SchedulerService(repository=repository, retention=retention, stale_timeout=timedelta(minutes=30))

    await service.tick()

    repository.enqueue_due.assert_awaited_once()
    repository.recover_stale.assert_awaited_once()
    retention.assert_awaited_once()


@pytest.mark.asyncio
async def test_scheduler_stops_after_current_tick():
    stop_event = asyncio.Event()
    repository = SimpleNamespace(enqueue_due=AsyncMock(side_effect=lambda *_: stop_event.set()), recover_stale=AsyncMock())
    service = SchedulerService(repository=repository, retention=AsyncMock(), stale_timeout=timedelta(minutes=30), poll_seconds=0)

    await service.run(stop_event)

    assert repository.enqueue_due.await_count == 1
