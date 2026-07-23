from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.infoservice.bot.handlers import reports
from src.infoservice.bot.states import CreateReport


@pytest.mark.asyncio
async def test_report_wizard_commits_only_after_confirmation(monkeypatch):
    created = []

    class Repository:
        def __init__(self, session):
            pass

        async def create(self, user_id, draft):
            created.append((user_id, draft))
            return SimpleNamespace(id=uuid4(), name=draft.name, enabled=True)

    class State:
        data = {}
        cleared = False
        value = None

        async def set_state(self, value): self.value = value
        async def update_data(self, **data): self.data.update(data)
        async def get_data(self): return self.data
        async def clear(self): self.cleared = True

    class Message:
        text = "AI"
        async def answer(self, *_args, **_kwargs): pass

    class Callback:
        message = Message()
        async def answer(self, *_args, **_kwargs): pass

    monkeypatch.setattr(reports, "ReportRepository", Repository)
    state = State()
    await reports.begin_create_report(Callback(), state)
    assert state.data == {}
    await reports.receive_report_name(Message(), state)
    assert created == []
    await reports.confirm_create_report(Callback(), state, object(), SimpleNamespace(id="user-id", timezone="UTC"))

    assert [item[1].name for item in created] == ["AI"]
    assert created[0][1].next_run_at is not None
    assert state.cleared is True
    assert CreateReport.name.state.endswith(":name")


@pytest.mark.asyncio
async def test_foreign_report_callback_is_hidden(monkeypatch):
    class Repository:
        def __init__(self, session): pass
        async def get_owned(self, *_args):
            from src.infoservice.errors import NotFound
            raise NotFound("Отчёт не найден")

    class Callback:
        data = f"report:view:{uuid4()}"
        calls = []
        async def answer(self, text=None, **kwargs): self.calls.append((text, kwargs))

    monkeypatch.setattr(reports, "ReportRepository", Repository)
    callback = Callback()
    await reports.view_report(callback, object(), SimpleNamespace(id="user-id"))

    assert callback.calls == [("Отчёт не найден", {"show_alert": True})]


@pytest.mark.asyncio
async def test_manual_run_requires_credential(monkeypatch):
    report = SimpleNamespace(id=uuid4())

    class Repository:
        def __init__(self, session): pass
        async def get_owned(self, *_args): return report

    class Session:
        async def scalar(self, *_args): return None

    class Callback:
        data = f"report:run:{report.id}"
        calls = []
        async def answer(self, text=None, **kwargs): self.calls.append((text, kwargs))

    monkeypatch.setattr(reports, "ReportRepository", Repository)
    callback = Callback()
    await reports.manual_run(callback, Session(), SimpleNamespace(id=uuid4()))
    assert callback.calls == [("Для запуска добавьте ключ DeepSeek.", {"show_alert": True})]


@pytest.mark.asyncio
async def test_newreport_command_starts_name_state():
    replies = []

    class Message:
        async def answer(self, text, **kwargs):
            replies.append((text, kwargs))

    class State:
        value = None

        async def clear(self):
            self.value = None

        async def set_state(self, value):
            self.value = value

    state = State()
    await reports.new_report_command(Message(), state)

    assert state.value == CreateReport.name
    assert "название" in replies[-1][0].lower()


@pytest.mark.asyncio
async def test_reports_command_clears_state_and_lists_owned_reports(monkeypatch):
    owned_reports = [SimpleNamespace(id=uuid4(), name="Python")]

    class Repository:
        def __init__(self, _session):
            pass

        async def list_owned(self, user_id):
            assert user_id == "user-id"
            return owned_reports

    class Message:
        replies = []

        async def answer(self, text, **kwargs):
            self.replies.append((text, kwargs))

    class State:
        cleared = False

        async def clear(self):
            self.cleared = True

    monkeypatch.setattr(reports, "ReportRepository", Repository)
    message = Message()
    state = State()
    await reports.reports_command(
        message, state, object(), SimpleNamespace(id="user-id")
    )

    assert state.cleared is True
    callbacks = [
        button.callback_data
        for row in message.replies[-1][1]["reply_markup"].inline_keyboard
        for button in row
    ]
    assert f"report:view:{owned_reports[0].id}" in callbacks
