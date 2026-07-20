from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.db.models import Report, ReportRun
from src.infoservice.errors import NotFound


class RunRepository:
    """Worker-only access to runs; user-facing code must use ReportRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_report(self, report_id: UUID) -> Report:
        report = await self.session.get(Report, report_id)
        if report is None:
            raise NotFound("Отчёт не найден")
        return report

    async def get(self, run_id: UUID) -> ReportRun:
        run = await self.session.get(ReportRun, run_id)
        if run is None:
            raise NotFound("Запуск не найден")
        return run
