from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.infoservice.db.session import create_session_factory


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL tests")
    session_factory = create_session_factory(database_url)
    async with session_factory() as database_session:
        await database_session.execute(text("TRUNCATE TABLE users CASCADE"))
        await database_session.commit()
        try:
            yield database_session
        finally:
            await database_session.rollback()
            await database_session.execute(text("TRUNCATE TABLE users CASCADE"))
            await database_session.commit()


@pytest_asyncio.fixture
async def report(session: AsyncSession):
    from src.infoservice.db.models import Report, User

    user = User(telegram_user_id=1002, chat_id=1002, timezone="UTC")
    report = Report(user=user, name="Test report", schedule_kind="daily", schedule_value="10:00")
    session.add(report)
    await session.commit()
    return report
