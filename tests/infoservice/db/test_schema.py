from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from src.infoservice.db.models import Report, ReportRun, User


@pytest.mark.asyncio
async def test_user_and_report_cascade(session):
    user = User(telegram_user_id=1001, chat_id=1001, timezone="Europe/Moscow")
    report = Report(user=user, name="AI", schedule_kind="daily", schedule_value="09:00")
    session.add(user)
    await session.commit()

    await session.delete(user)
    await session.commit()

    assert await session.get(Report, report.id) is None


@pytest.mark.asyncio
async def test_scheduled_run_is_idempotent(session, report):
    scheduled_for = datetime(2026, 7, 20, 6, tzinfo=timezone.utc)
    session.add_all([
        ReportRun(report_id=report.id, trigger="scheduled", scheduled_for=scheduled_for),
        ReportRun(report_id=report.id, trigger="scheduled", scheduled_for=scheduled_for),
    ])

    with pytest.raises(IntegrityError):
        await session.commit()
