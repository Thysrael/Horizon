from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.infoservice.bot.keyboards import (
    accepted_value_menu,
    delete_confirmation_menu,
    field_menu,
    primary_input_menu,
    source_catalog_menu,
    source_menu,
    source_options_menu,
    summary_menu,
)
from src.infoservice.bot.handlers import sources
from src.infoservice.bot.states import SourceForm


def labels(markup):
    return [button.text for row in markup.inline_keyboard for button in row]


def test_source_wizard_has_explicit_states():
    assert SourceForm.primary_input.state.endswith(":primary_input")
    assert SourceForm.value_review.state.endswith(":value_review")
    assert SourceForm.options.state.endswith(":options")
    assert SourceForm.field_input.state.endswith(":field_input")
    assert SourceForm.summary.state.endswith(":summary")


def test_catalog_contains_only_four_stable_sources():
    assert labels(source_catalog_menu("report-id")) == [
        "🟠 RSS / Atom",
        "🔵 Telegram-канал",
        "⚫ GitHub",
        "🟠 Hacker News",
        "‹ Назад",
        "Отмена",
    ]


@pytest.mark.asyncio
async def test_legacy_open_catalog_signature_uses_stable_labels(monkeypatch):
    report_id = uuid4()

    class Repository:
        def __init__(self, session):
            pass

        async def get_owned(self, *_args):
            return object()

    class Message:
        answers = []

        async def answer(self, text, **kwargs):
            self.answers.append((text, kwargs))

    class Callback:
        data = f"source:catalog:{report_id}"
        message = Message()

        async def answer(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    callback = Callback()

    await sources.open_catalog(
        callback,
        object(),
        SimpleNamespace(id=uuid4()),
        SimpleNamespace(enable_twitter=False, enable_openbb=False),
    )

    markup = callback.message.answers[0][1]["reply_markup"]
    assert labels(markup)[:4] == [
        "🟠 RSS / Atom",
        "🔵 Telegram-канал",
        "⚫ GitHub",
        "🟠 Hacker News",
    ]


def test_delete_confirmation_has_source_flow_controls():
    markup = delete_confirmation_menu()
    buttons = [button for row in markup.inline_keyboard for button in row]

    assert [button.text for button in buttons] == ["Да, удалить", "‹ Назад", "Отмена"]
    assert [button.callback_data for button in buttons] == [
        "source:delete-confirm",
        "source:back",
        "cancel",
    ]


def test_first_two_steps_have_explicit_next_action():
    assert "Далее →" in labels(accepted_value_menu())
    assert "Далее →" in labels(source_options_menu())
    assert labels(primary_input_menu()) == ["‹ Назад", "Отмена"]


def test_summary_and_edit_keyboards_are_human_readable():
    assert labels(summary_menu()) == [
        "✅ Сохранить источник", "✏️ Изменить", "‹ Назад", "Отмена",
    ]
    assert labels(field_menu("telegram")) == [
        "Категория", "Количество сообщений", "Готово", "‹ Назад", "Отмена",
    ]


def test_beta_source_has_no_edit_button():
    assert "Изменить" not in labels(source_menu("source-id", True, editable=False))
