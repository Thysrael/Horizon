import os
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.infoservice.db.models import Report, ReportRun, User
from src.infoservice.db.session import create_session_factory


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest_asyncio.fixture
async def session_factory() -> async_sessionmaker:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL tests")
    factory = create_session_factory(database_url)
    async with factory.begin() as session:
        await session.execute(text("TRUNCATE TABLE users CASCADE"))
    yield factory
    async with factory.begin() as session:
        await session.execute(text("TRUNCATE TABLE users CASCADE"))


@pytest_asyncio.fixture
async def due_report(session_factory):
    due_at = utcnow() - timedelta(hours=2)
    async with session_factory.begin() as session:
        user = User(telegram_user_id=8801, chat_id=8801, timezone="UTC")
        report = Report(
            user=user,
            name="Due report",
            schedule_kind="daily",
            schedule_value="09:00",
            timezone="UTC",
            next_run_at=due_at,
        )
        session.add(report)
    return report, due_at


@pytest_asyncio.fixture
async def queued_runs(session_factory):
    now = utcnow()
    async with session_factory.begin() as session:
        user = User(telegram_user_id=8802, chat_id=8802, timezone="UTC")
        report = Report(user=user, name="Claim report", schedule_kind="daily", schedule_value="09:00")
        session.add_all(
            [
                ReportRun(report=report, trigger="scheduled", scheduled_for=now - timedelta(minutes=2)),
                ReportRun(report=report, trigger="manual", scheduled_for=now - timedelta(minutes=1)),
            ]
        )
    return report
