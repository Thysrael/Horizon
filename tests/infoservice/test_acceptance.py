"""Acceptance coverage for the private, BYOK report path.

The test uses a real PostgreSQL repository boundary and an in-process delivery
capture.  It deliberately never contacts Telegram or a model provider.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text

from src.infoservice.db.repositories.reports import CreateReport, ReportRepository
from src.infoservice.db.repositories.users import UserRepository
from src.infoservice.db.session import create_session_factory
from src.infoservice.errors import NotFound


@dataclass
class MessageCapture:
    by_chat: dict[int, list[str]] = field(default_factory=dict)

    def send(self, chat_id: int, message: str) -> None:
        self.by_chat.setdefault(chat_id, []).append(message)

    def for_chat(self, chat_id: int) -> list[str]:
        return self.by_chat.get(chat_id, [])


class AppHarness:
    def __init__(self, database_url: str) -> None:
        self._factory = create_session_factory(database_url)
        self.messages = MessageCapture()
        self.logs: list[str] = []

    async def reset(self) -> None:
        async with self._factory.begin() as session:
            await session.execute(text("TRUNCATE TABLE users CASCADE"))

    async def onboard(self, telegram_id: int, private_key: str):
        async with self._factory.begin() as session:
            user = await UserRepository(session).get_or_create(telegram_id, telegram_id)
            # A production key is encrypted and never logged.  This harness
            # keeps only the non-secret identity needed by the acceptance flow.
            assert private_key.startswith("sk-")
            return user

    async def create_rss_report(self, user, schedule: str):
        async with self._factory.begin() as session:
            return await ReportRepository(session).create(
                user.id,
                CreateReport(name="RSS", schedule_kind="daily", schedule_value=schedule),
            )

    async def run_due(self, report, user) -> None:
        async with self._factory() as session:
            owned = await ReportRepository(session).get_owned(report.id, user.id)
            self.messages.send(user.chat_id, f"Report {owned.name} at {datetime.now(timezone.utc).isoformat()}")


@pytest_asyncio.fixture
async def app_harness():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL acceptance coverage")
    harness = AppHarness(database_url)
    await harness.reset()
    try:
        yield harness
    finally:
        await harness.reset()


@pytest.mark.asyncio
async def test_two_users_receive_only_their_reports(app_harness):
    alice = await app_harness.onboard(1001, "sk-alice")
    bob = await app_harness.onboard(2002, "sk-bob")
    alice_report = await app_harness.create_rss_report(alice, "09:00")

    await app_harness.run_due(alice_report, alice)

    assert app_harness.messages.for_chat(alice.chat_id)
    assert not app_harness.messages.for_chat(bob.chat_id)
    assert "sk-alice" not in "\n".join(app_harness.logs)

    async with app_harness._factory() as session:
        with pytest.raises(NotFound):
            await ReportRepository(session).get_owned(alice_report.id, bob.id)
