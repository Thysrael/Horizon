from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import aliased

from src.infoservice.db.models import Report, ReportRun, RunStatus, RunTrigger, User

from .calculator import ScheduleSpec, next_occurrence


@dataclass(frozen=True, slots=True)
class ClaimedRun:
    id: UUID
    report_id: UUID
    scheduled_for: datetime
    worker_id: str
    started_at: datetime


class SchedulerRepository:
    """Creates durable scheduled runs using short PostgreSQL transactions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def enqueue_due(self, now: datetime, limit: int) -> list[UUID]:
        now = _as_utc(now)
        if limit < 1:
            return []
        async with self.session_factory.begin() as session:
            statement = (
                select(Report)
                .where(Report.enabled.is_(True), Report.next_run_at.is_not(None), Report.next_run_at <= now)
                .order_by(Report.next_run_at, Report.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            reports = (await session.scalars(statement)).all()
            run_ids: list[UUID] = []
            for report in reports:
                scheduled_for = report.next_run_at
                assert scheduled_for is not None
                run = ReportRun(
                    report_id=report.id,
                    trigger=RunTrigger.SCHEDULED,
                    scheduled_for=scheduled_for,
                    status=RunStatus.QUEUED,
                )
                session.add(run)
                await session.flush()
                run_ids.append(run.id)
                report.next_run_at = next_occurrence(
                    ScheduleSpec(report.schedule_kind.value, report.schedule_value, report.timezone or "UTC"), now
                )
            return run_ids


class RunRepository:
    """Atomically claims queued report runs for independent workers."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def claim_next(self, worker_id: str, now: datetime) -> ClaimedRun | None:
        now = _as_utc(now)
        async with self.session_factory.begin() as session:
            running_run = aliased(ReportRun)
            running_report = aliased(Report)
            statement = (
                select(ReportRun)
                .join(Report, ReportRun.report_id == Report.id)
                .join(User, Report.user_id == User.id)
                .where(
                    ReportRun.status == RunStatus.QUEUED,
                    ReportRun.scheduled_for <= now,
                    ~exists(
                        select(1)
                        .select_from(running_run)
                        .join(running_report, running_run.report_id == running_report.id)
                        .where(
                            running_report.user_id == User.id,
                            running_run.status == RunStatus.RUNNING,
                        )
                    ),
                )
                .order_by(ReportRun.scheduled_for, ReportRun.created_at, ReportRun.id)
                .limit(1)
                .with_for_update(of=User, skip_locked=True)
            )
            run = (await session.scalars(statement)).one_or_none()
            if run is None:
                return None
            run.status = RunStatus.RUNNING
            run.worker_id = worker_id
            run.started_at = now
            run.heartbeat_at = now
            await session.flush()
            return ClaimedRun(run.id, run.report_id, run.scheduled_for, worker_id, now)

    async def touch_claim(self, claim: ClaimedRun, now: datetime) -> bool:
        """Renew a running claim without allowing a former worker to revive it."""
        now = _as_utc(now)
        async with self.session_factory.begin() as session:
            result = await session.execute(
                update(ReportRun)
                .where(
                    ReportRun.id == claim.id,
                    ReportRun.status == RunStatus.RUNNING,
                    ReportRun.worker_id == claim.worker_id,
                )
                .values(heartbeat_at=now)
            )
            return result.rowcount == 1

    async def recover_stale(self, now: datetime, timeout: timedelta) -> int:
        now = _as_utc(now)
        cutoff = now - timeout
        async with self.session_factory.begin() as session:
            statement = (
                select(ReportRun)
                .where(
                    ReportRun.status == RunStatus.RUNNING,
                    func.coalesce(ReportRun.heartbeat_at, ReportRun.started_at) < cutoff,
                )
                .order_by(func.coalesce(ReportRun.heartbeat_at, ReportRun.started_at), ReportRun.id)
                .with_for_update(skip_locked=True)
            )
            runs = (await session.scalars(statement)).all()
            for run in runs:
                run.attempt_count += 1
                if run.attempt_count < 2:
                    run.status = RunStatus.QUEUED
                    run.worker_id = None
                    run.started_at = None
                    run.heartbeat_at = None
                else:
                    run.status = RunStatus.FAILED
                    run.finished_at = now
                    run.error_summary = "Run abandoned after stale worker recovery"
            return len(runs)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)
