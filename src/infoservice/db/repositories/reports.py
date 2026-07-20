from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.db.models import Report, Source, User
from src.infoservice.errors import LimitExceeded, NotFound


@dataclass(frozen=True, slots=True)
class CreateReport:
    name: str
    enabled: bool = True
    language: str = "en"
    lookback_hours: int = 24
    ai_score_threshold: float = 7.0
    max_items: int = 10
    categories: list[str] | None = None
    exclusions: list[str] | None = None
    custom_instruction: str | None = None
    schedule_kind: str = "daily"
    schedule_value: str = "09:00"
    timezone: str | None = None
    next_run_at: Any = None


@dataclass(frozen=True, slots=True)
class UpdateReport:
    name: str | None = None
    enabled: bool | None = None
    language: str | None = None
    lookback_hours: int | None = None
    ai_score_threshold: float | None = None
    max_items: int | None = None
    categories: list[str] | None = None
    exclusions: list[str] | None = None
    custom_instruction: str | None = None
    schedule_kind: str | None = None
    schedule_value: str | None = None
    timezone: str | None = None
    next_run_at: Any = None


@dataclass(frozen=True, slots=True)
class CreateSource:
    source_type: str
    display_name: str
    config: dict[str, Any]
    enabled: bool = True


class ReportRepository:
    max_reports_per_user = 5
    max_sources_per_report = 30

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_owned(self, report_id: UUID, user_id: UUID) -> Report:
        stmt = select(Report).where(Report.id == report_id, Report.user_id == user_id)
        report = (await self.session.execute(stmt)).scalar_one_or_none()
        if report is None:
            raise NotFound("Отчёт не найден")
        return report

    async def create(self, user_id: UUID, data: CreateReport) -> Report:
        await self._lock_user(user_id)
        count = await self.session.scalar(select(func.count()).select_from(Report).where(Report.user_id == user_id))
        if count >= self.max_reports_per_user:
            raise LimitExceeded(f"Можно создать не более {self.max_reports_per_user} отчётов")
        report = Report(user_id=user_id, **self._create_values(data))
        self.session.add(report)
        await self.session.flush()
        return report

    async def update(self, report_id: UUID, user_id: UUID, data: UpdateReport) -> Report:
        report = await self.get_owned(report_id, user_id)
        for field in fields(data):
            value = getattr(data, field.name)
            if value is not None:
                setattr(report, field.name, value)
        await self.session.flush()
        return report

    async def delete(self, report_id: UUID, user_id: UUID) -> None:
        report = await self.get_owned(report_id, user_id)
        await self.session.delete(report)
        await self.session.flush()

    async def add_source(self, report_id: UUID, user_id: UUID, data: CreateSource) -> Source:
        await self._lock_user(user_id)
        report = await self.get_owned(report_id, user_id)
        count = await self.session.scalar(select(func.count()).select_from(Source).where(Source.report_id == report.id))
        if count >= self.max_sources_per_report:
            raise LimitExceeded(f"В отчёте может быть не более {self.max_sources_per_report} источников")
        source = Source(report_id=report.id, **self._create_values(data))
        self.session.add(source)
        await self.session.flush()
        return source

    async def _lock_user(self, user_id: UUID) -> User:
        stmt = select(User).where(User.id == user_id).with_for_update()
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if user is None:
            raise NotFound("Пользователь не найден")
        return user

    @staticmethod
    def _create_values(data: Any) -> dict[str, Any]:
        values = {field.name: getattr(data, field.name) for field in fields(data)}
        return {key: value for key, value in values.items() if value is not None}
