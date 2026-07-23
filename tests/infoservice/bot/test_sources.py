from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.infoservice.bot.handlers import sources
from src.infoservice.db.repositories.reports import ReportRepository


class FakeMessage:
    def __init__(self):
        self.answers = []

    async def edit_text(self, text, **kwargs):
        self.answers.append((text, kwargs))
        return self


class FakeCallback:
    def __init__(self, data):
        self.data = data
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None, **kwargs):
        self.answers.append((text, kwargs))


def button_labels(message):
    markup = message.answers[-1][1]["reply_markup"]
    return [button.text for row in markup.inline_keyboard for button in row]


@pytest.mark.asyncio
async def test_catalog_refuses_creation_at_repository_limit(monkeypatch):
    report_id = uuid4()
    user_id = uuid4()

    class Repository:
        max_sources_per_report = ReportRepository.max_sources_per_report

        def __init__(self, _session):
            pass

        async def get_owned(self, candidate_report, candidate_user):
            assert (candidate_report, candidate_user) == (report_id, user_id)
            return object()

        async def list_sources(self, candidate_report, candidate_user):
            assert (candidate_report, candidate_user) == (report_id, user_id)
            return [object()] * self.max_sources_per_report

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    callback = FakeCallback(f"source:catalog:{report_id}")

    await sources.open_catalog(
        callback,
        object(),
        SimpleNamespace(id=user_id),
        SimpleNamespace(enable_twitter=True, enable_openbb=True),
    )

    assert callback.message.answers == []
    assert callback.answers == [
        ("В отчёте может быть не более 30 источников", {"show_alert": True})
    ]


@pytest.mark.asyncio
async def test_catalog_calls_stable_menu_with_report_only(monkeypatch):
    report_id = uuid4()
    calls = []

    class Repository:
        max_sources_per_report = 30

        def __init__(self, _session):
            pass

        async def get_owned(self, *_args):
            return object()

        async def list_sources(self, *_args):
            return []

    def catalog_menu(candidate_report):
        calls.append(candidate_report)
        return "stable-menu"

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    monkeypatch.setattr(sources, "source_catalog_menu", catalog_menu)
    callback = FakeCallback(f"source:catalog:{report_id}")

    await sources.open_catalog(
        callback,
        object(),
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(enable_twitter=True, enable_openbb=True),
    )

    assert calls == [str(report_id)]
    assert callback.message.answers[-1][1]["reply_markup"] == "stable-menu"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source_type", "config", "editable", "card_fragment"),
    [
        (
            "telegram",
            {"channel": "python_news", "fetch_limit": 20},
            True,
            "Канал: @python_news",
        ),
        ("reddit", {"subreddit": "python"}, False, "Legacy Reddit\nТип: reddit"),
    ],
)
async def test_source_card_respects_stability(
    monkeypatch, source_type, config, editable, card_fragment
):
    source_id = uuid4()

    class Repository:
        def __init__(self, _session):
            pass

        async def get_source_owned(self, *_args):
            return SimpleNamespace(
                id=source_id,
                display_name="Legacy Reddit",
                source_type=source_type,
                config=config,
                enabled=True,
            )

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    callback = FakeCallback(f"source:view:{source_id}")

    await sources.view_source(callback, object(), SimpleNamespace(id=uuid4()))

    assert card_fragment in callback.message.answers[-1][0]
    labels = button_labels(callback.message)
    assert ("Изменить" in labels) is editable


@pytest.mark.asyncio
async def test_sources_command_lists_owned_reports(monkeypatch):
    reports = [SimpleNamespace(id=uuid4(), name="Python"), SimpleNamespace(id=uuid4(), name="AI")]

    class Repository:
        def __init__(self, _session):
            pass

        async def list_owned(self, user_id):
            assert user_id == "user-id"
            return reports

    class Message:
        answers = []

        async def answer(self, text, **kwargs):
            self.answers.append((text, kwargs))

    class State:
        cleared = False

        async def clear(self):
            self.cleared = True

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    message = Message()
    state = State()
    await sources.sources_command(message, state, object(), SimpleNamespace(id="user-id"))

    assert state.cleared is True
    callbacks = [
        button.callback_data
        for row in message.answers[-1][1]["reply_markup"].inline_keyboard
        for button in row
    ]
    assert callbacks == [f"source:list:{report.id}" for report in reports]
