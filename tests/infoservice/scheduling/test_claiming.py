import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from src.infoservice.db.models import Report, ReportRun, RunStatus
from src.infoservice.scheduling.repository import RunRepository, SchedulerRepository



def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_enqueue_due_is_idempotent_and_advances_schedule(session_factory, due_report):
    report, due_at = due_report
    repository = SchedulerRepository(session_factory)

    first = await repository.enqueue_due(utcnow(), limit=10)
    second = await repository.enqueue_due(utcnow(), limit=10)

    assert len(first) == 1
    assert second == []
    async with session_factory() as session:
        run = await session.get(ReportRun, first[0])
        refreshed_report = await session.get(Report, report.id)
    assert run.scheduled_for == due_at
    assert refreshed_report.next_run_at > utcnow()


@pytest.mark.asyncio
async def test_two_claimers_receive_different_runs(session_factory, queued_runs):
    run_repo = RunRepository(session_factory)

    first, second = await asyncio.gather(
        run_repo.claim_next("worker-a", utcnow()),
        run_repo.claim_next("worker-b", utcnow()),
    )

    assert first is not None
    assert second is not None
    assert first.id != second.id


@pytest.mark.asyncio
async def test_recover_stale_requeues_once_then_fails_safely(session_factory, queued_runs):
    now = utcnow()
    async with session_factory.begin() as session:
        run = (await session.scalars(select(ReportRun).limit(1))).one()
        run_id = run.id
        run.status = RunStatus.RUNNING
        run.started_at = now - timedelta(hours=2)

    repository = RunRepository(session_factory)
    assert await repository.recover_stale(now, timedelta(minutes=30)) == 1
    async with session_factory() as session:
        run = await session.get(ReportRun, run_id)
        assert run is not None
        assert run.status == RunStatus.QUEUED
        assert run.attempt_count == 1
        run.status = RunStatus.RUNNING
        run.started_at = now - timedelta(hours=2)
        run.attempt_count = 1
        await session.commit()

    assert await repository.recover_stale(now, timedelta(minutes=30)) == 1
    async with session_factory() as session:
        run = await session.get(ReportRun, run_id)
        assert run is not None
    assert run.status == RunStatus.FAILED
    assert run.attempt_count == 2
