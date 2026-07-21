"""Transactional creation of a user-requested report run."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.db.models import Report, ReportRun, RunStatus, RunTrigger, User
from src.infoservice.errors import NotFound


class ManualRunResult(str, Enum):
    ENQUEUED = "enqueued"
    COOLDOWN = "cooldown"


class ManualRunRepository:
    """Serialize a user's manual launches on the owning ``users`` row.

    The lock covers both predicates and insertion, so concurrent callback
    transactions cannot each observe an empty queue and create a run.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue(self, user_id: UUID, report_id: UUID, now: datetime) -> ManualRunResult:
        await self._lock_user(user_id)
        report = await self.session.scalar(select(Report).where(Report.id == report_id, Report.user_id == user_id))
        if report is None:
            raise NotFound("Отчёт не найден")
        running = await self.session.scalar(
            select(ReportRun.id)
            .join(Report)
            .where(
                Report.user_id == user_id,
                ReportRun.status.in_((RunStatus.QUEUED, RunStatus.RUNNING)),
            )
            .limit(1)
        )
        recent = await self.session.scalar(
            select(ReportRun.id)
            .where(ReportRun.report_id == report_id, ReportRun.scheduled_for >= now - timedelta(hours=1))
            .limit(1)
        )
        if running is not None or recent is not None:
            return ManualRunResult.COOLDOWN
        self.session.add(ReportRun(report_id=report_id, trigger=RunTrigger.MANUAL, scheduled_for=now))
        await self.session.flush()
        return ManualRunResult.ENQUEUED

    async def _lock_user(self, user_id: UUID) -> None:
        user = await self.session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            raise NotFound("Пользователь не найден")
