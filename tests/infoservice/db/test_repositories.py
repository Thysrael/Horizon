from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.infoservice.db.repositories.reports import CreateReport, ReportRepository
from src.infoservice.db.repositories.users import UserRepository
from src.infoservice.errors import LimitExceeded, NotFound


@pytest_asyncio.fixture
async def user_a(session: AsyncSession):
    return await UserRepository(session).get_or_create(10001, 10001)


@pytest_asyncio.fixture
async def user_b(session: AsyncSession):
    return await UserRepository(session).get_or_create(10002, 10002)


@pytest_asyncio.fixture
async def report_repo(session: AsyncSession) -> ReportRepository:
    return ReportRepository(session)


@pytest.mark.asyncio
async def test_get_owned_hides_foreign_report(report_repo, user_a, user_b):
    report = await report_repo.create(user_a.id, CreateReport(name="AI"))

    with pytest.raises(NotFound, match="Отчёт не найден"):
        await report_repo.get_owned(report.id, user_b.id)


@pytest.mark.asyncio
async def test_report_limit_is_enforced(report_repo, user_a):
    for index in range(5):
        await report_repo.create(user_a.id, CreateReport(name=f"R{index}"))

    with pytest.raises(LimitExceeded, match="5"):
        await report_repo.create(user_a.id, CreateReport(name="R6"))
