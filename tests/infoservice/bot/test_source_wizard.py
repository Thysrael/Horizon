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
from src.infoservice.bot.handlers import source_wizard, sources
from src.infoservice.bot.states import SourceForm
from src.infoservice.errors import LimitExceeded


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
async def test_open_catalog_uses_stable_labels(monkeypatch):
    report_id = uuid4()

    class Repository:
        def __init__(self, session):
            pass

        async def get_owned(self, *_args):
            return object()

        async def list_sources(self, *_args):
            return []

    class Message:
        answers = []

        async def edit_text(self, text, **kwargs):
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
        "source:delete-back",
        "cancel",
    ]


@pytest.mark.asyncio
async def test_delete_back_clears_confirmation_and_restores_owned_source_card(monkeypatch):
    source_id = uuid4()
    user = SimpleNamespace(id=uuid4())

    class Repository:
        def __init__(self, session):
            pass

        async def get_source_owned(self, requested_source_id, requested_user_id):
            assert requested_source_id == source_id
            assert requested_user_id == user.id
            return SimpleNamespace(
                id=source_id,
                display_name="Python News",
                source_type="telegram",
                config={"channel": "python_news", "fetch_limit": 20},
                enabled=True,
            )

    class State:
        cleared = False

        async def get_data(self):
            return {"source_delete_id": str(source_id)}

        async def clear(self):
            self.cleared = True

    class Message:
        answers = []

        async def edit_text(self, text, **kwargs):
            self.answers.append((text, kwargs))

    class Callback:
        message = Message()
        answered = False

        async def answer(self, *_args, **_kwargs):
            self.answered = True

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    state = State()
    callback = Callback()

    await sources.return_to_source_from_delete(callback, state, object(), user)

    assert state.cleared is True
    assert callback.answered is True
    assert callback.message.answers[0][0].startswith(
        "Telegram-канал\nКанал: @python_news"
    )
    assert labels(callback.message.answers[0][1]["reply_markup"]) == [
        "Изменить", "Отключить", "Удалить", "‹ Главное меню",
    ]


@pytest.mark.asyncio
async def test_dispatcher_routes_delete_confirmation_callbacks_before_delete_prefix(
    monkeypatch,
):
    """Exact delete callbacks must win over the broad source:delete: route."""
    source_id = uuid4()
    user = SimpleNamespace(id=uuid4())
    deleted = []

    class Repository:
        def __init__(self, session):
            pass

        async def get_source_owned(self, requested_source_id, requested_user_id):
            assert (requested_source_id, requested_user_id) == (source_id, user.id)
            return SimpleNamespace(
                id=source_id,
                display_name="Python News",
                source_type="telegram",
                config={"channel": "python_news", "fetch_limit": 20},
                enabled=True,
            )

        async def delete_source(self, requested_source_id, requested_user_id):
            assert (requested_source_id, requested_user_id) == (source_id, user.id)
            deleted.append(source_id)

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    state = FakeState()
    message = FakeMessage()

    for data, raw_state in [
        (f"source:delete:{source_id}", None),
        ("source:delete-back", SourceForm.delete_confirmation.state),
    ]:
        callback = FakeCallback(data, message)
        await sources.router.propagate_event(
            "callback_query",
            callback,
            state=state,
            session=object(),
            user=user,
            raw_state=raw_state,
        )

    assert message.answers[-1][0].startswith("Telegram-канал\nКанал: @python_news")
    assert state.cleared is True

    state.cleared = False
    await sources.router.propagate_event(
        "callback_query",
        FakeCallback(f"source:delete:{source_id}", message),
        state=state,
        session=object(),
        user=user,
        raw_state=None,
    )
    await sources.router.propagate_event(
        "callback_query",
        FakeCallback("source:delete-confirm", message),
        state=state,
        session=object(),
        user=user,
        raw_state=SourceForm.delete_confirmation.state,
    )

    assert deleted == [source_id]
    assert message.answers[-1][0] == "Источник удалён."


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


class FakeState:
    def __init__(self):
        self.data = {}
        self.value = None
        self.cleared = False

    async def update_data(self, **values):
        self.data.update(values)

    async def get_data(self):
        return self.data

    async def set_state(self, value):
        self.value = value

    async def clear(self):
        self.data = {}
        self.value = None
        self.cleared = True


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))
        return self

    async def edit_text(self, text, **kwargs):
        self.answers.append((text, kwargs))
        return self


class FakeCallback:
    def __init__(self, data, message=None):
        self.data = data
        self.message = message or FakeMessage()
        self.answers = []

    async def answer(self, text=None, **kwargs):
        self.answers.append((text, kwargs))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source_type", "primary", "github_kind"),
    [
        ("rss", "https://example.com/feed.xml", None),
        ("telegram", "https://t.me/python_news", None),
        ("github", "pallets/flask", "repo_releases"),
        ("hackernews", None, None),
    ],
)
async def test_creation_flow_reaches_summary_without_writing(
    monkeypatch, source_type, primary, github_kind
):
    report_id = uuid4()
    state = FakeState()

    class Repository:
        def __init__(self, _session):
            pass

        async def get_owned(self, candidate, _user_id):
            assert candidate == report_id
            return SimpleNamespace(id=report_id)

        async def add_source(self, *_args):
            raise AssertionError("summary must not write")

    monkeypatch.setattr(source_wizard, "ReportRepository", Repository)
    if source_type == "rss":

        async def name(_url, _client=None):
            return "Example Feed"

        monkeypatch.setattr(source_wizard, "resolve_rss_name", name)

    start = FakeCallback(f"source:create:{source_type}:{report_id}")
    await source_wizard.begin_create(
        start, state, object(), SimpleNamespace(id=uuid4())
    )

    if github_kind:
        await source_wizard.choose_github_kind(
            FakeCallback(f"source:github-kind:{github_kind}"), state
        )
    if primary is not None:
        await source_wizard.receive_primary(FakeMessage(primary), state)
        assert state.value == SourceForm.value_review
        await source_wizard.accept_primary(FakeCallback("source:next"), state)
    await source_wizard.show_summary(
        FakeCallback("source:summary"),
        state,
        SimpleNamespace(enable_twitter=False, enable_openbb=False),
    )

    assert state.value == SourceForm.summary
    assert "{" not in state.data["last_card"]
    expected_progress = "Шаг 2 из 2" if source_type == "hackernews" else "Шаг 3 из 3"
    assert state.data["last_card"].startswith(expected_progress)


@pytest.mark.asyncio
async def test_invalid_primary_keeps_state_and_shows_example():
    state = FakeState()
    draft = source_wizard.SourceDraft.new(str(uuid4()), "telegram")
    await source_wizard.store_draft(state, draft, SourceForm.primary_input)
    message = FakeMessage("https://t.me/+private")

    await source_wizard.receive_primary(message, state)

    assert state.value == SourceForm.primary_input
    assert "@durov" in message.answers[-1][0]
    assert state.data["source_draft"]["values"]["fetch_limit"] == 20


@pytest.mark.asyncio
async def test_back_from_options_returns_to_value_review():
    state = FakeState()
    draft = source_wizard.SourceDraft.new(
        str(uuid4()), "telegram"
    ).with_values(channel="python_news")
    raw = draft.to_storage()
    raw.update(screen="options", history=["primary", "value_review"])
    await source_wizard.store_draft(
        state, source_wizard.SourceDraft.from_storage(raw), SourceForm.options
    )
    callback = FakeCallback("source:back")

    await source_wizard.go_back(callback, state)

    assert state.value == SourceForm.value_review
    assert "Принято" in callback.message.answers[-1][0]


@pytest.mark.asyncio
async def test_save_validates_then_creates_once(monkeypatch):
    report_id, user_id = uuid4(), uuid4()
    state = FakeState()
    draft = source_wizard.SourceDraft.new(
        str(report_id), "telegram"
    ).with_values(channel="python_news")
    await source_wizard.store_draft(state, draft, SourceForm.summary)
    created = []

    class Repository:
        def __init__(self, _session):
            pass

        async def add_source(self, candidate_report, candidate_user, data):
            created.append((candidate_report, candidate_user, data))
            return SimpleNamespace(id=uuid4(), enabled=True)

    monkeypatch.setattr(source_wizard, "ReportRepository", Repository)
    callback = FakeCallback("source:save")
    await source_wizard.save_source(
        callback,
        state,
        object(),
        SimpleNamespace(id=user_id),
        SimpleNamespace(enable_twitter=False, enable_openbb=False),
    )

    assert len(created) == 1
    assert created[0][0] == report_id
    assert created[0][1] == user_id
    assert created[0][2].config["channel"] == "python_news"
    assert state.cleared is True


@pytest.mark.asyncio
async def test_advanced_shows_supported_field_menu():
    state = FakeState()
    draft = source_wizard.SourceDraft.new(
        str(uuid4()), "telegram"
    ).with_values(channel="python_news")
    raw = draft.to_storage()
    raw.update(screen="options", history=["catalog", "primary", "value_review"])
    await source_wizard.store_draft(
        state, source_wizard.SourceDraft.from_storage(raw), SourceForm.options
    )
    callback = FakeCallback("source:advanced")

    await source_wizard.show_advanced(callback, state)

    assert state.value == SourceForm.options
    assert state.data["source_draft"]["screen"] == "advanced"
    assert "Выберите параметр" in callback.message.answers[-1][0]
    assert "source:field:fetch_limit" in str(
        callback.message.answers[-1][1]["reply_markup"]
    )


@pytest.mark.asyncio
async def test_field_error_preserves_draft_and_current_field():
    state = FakeState()
    draft = source_wizard.SourceDraft.new(str(uuid4()), "telegram").with_values(
        channel="python_news"
    )
    raw = draft.to_storage()
    raw["current_field"] = "fetch_limit"
    await source_wizard.store_draft(
        state, source_wizard.SourceDraft.from_storage(raw), SourceForm.field_input
    )
    message = FakeMessage("13")

    await source_wizard.receive_field(message, state)

    assert state.value == SourceForm.field_input
    assert state.data["source_draft"]["values"]["fetch_limit"] == 20
    assert "20" in message.answers[-1][0]


@pytest.mark.asyncio
async def test_valid_field_requires_next_before_returning_to_options():
    state = FakeState()
    draft = source_wizard.SourceDraft.new(str(uuid4()), "telegram").with_values(
        channel="python_news"
    )
    raw = draft.to_storage()
    raw["current_field"] = "fetch_limit"
    await source_wizard.store_draft(
        state, source_wizard.SourceDraft.from_storage(raw), SourceForm.field_input
    )
    message = FakeMessage("50")

    await source_wizard.receive_field(message, state)

    assert state.value == SourceForm.value_review
    assert state.data["source_draft"]["values"]["fetch_limit"] == 50
    assert "Далее →" in labels(message.answers[-1][1]["reply_markup"])


@pytest.mark.asyncio
async def test_back_from_field_input_returns_to_advanced_field_menu():
    state = FakeState()
    draft = source_wizard.SourceDraft.new(str(uuid4()), "telegram").with_values(
        channel="python_news"
    )
    raw = draft.to_storage()
    raw.update(
        current_field="fetch_limit",
        screen="field_input",
        history=["catalog", "primary", "value_review", "options", "advanced"],
    )
    await source_wizard.store_draft(
        state, source_wizard.SourceDraft.from_storage(raw), SourceForm.field_input
    )

    callback = FakeCallback("source:back")
    await source_wizard.go_back(callback, state)

    assert state.value == SourceForm.options
    assert state.data["source_draft"]["screen"] == "advanced"
    assert "source:field:fetch_limit" in str(
        callback.message.answers[-1][1]["reply_markup"]
    )


@pytest.mark.asyncio
async def test_back_from_advanced_returns_to_summary_when_editing_summary():
    state = FakeState()
    draft = source_wizard.SourceDraft.new(str(uuid4()), "telegram").with_values(
        channel="python_news"
    )
    raw = draft.to_storage()
    raw.update(screen="advanced", history=["catalog", "primary", "value_review", "options", "summary"])
    await state.update_data(
        source_draft=raw,
        last_card="Шаг 3 из 3\n\nTelegram-канал",
    )
    await state.set_state(SourceForm.options)

    callback = FakeCallback("source:back")
    await source_wizard.go_back(callback, state)

    assert state.value == SourceForm.summary
    assert callback.message.answers[-1][0] == "Шаг 3 из 3\n\nTelegram-канал"
    assert "✅ Сохранить источник" in labels(
        callback.message.answers[-1][1]["reply_markup"]
    )


@pytest.mark.asyncio
async def test_edit_stable_source_starts_from_existing_config(monkeypatch):
    source_id = uuid4()
    state = FakeState()
    source = SimpleNamespace(
        id=source_id,
        source_type="telegram",
        config={"channel": "python_news", "fetch_limit": 20},
        enabled=True,
    )

    class Repository:
        def __init__(self, _session):
            pass

        async def get_source_owned(self, candidate, _user_id):
            assert candidate == source_id
            return source

    monkeypatch.setattr(source_wizard, "ReportRepository", Repository)
    await source_wizard.begin_edit(
        FakeCallback(f"source:edit:{source_id}"),
        state,
        object(),
        SimpleNamespace(id=uuid4()),
    )

    raw = state.data["source_draft"]
    assert raw["mode"] == "edit"
    assert raw["values"]["channel"] == "python_news"
    assert state.value == SourceForm.options


@pytest.mark.asyncio
async def test_back_from_edit_summary_returns_to_source_card():
    source_id = uuid4()
    state = FakeState()
    draft = source_wizard.SourceDraft.edit(
        str(source_id),
        "telegram",
        {"channel": "python_news", "fetch_limit": 20},
        enabled=True,
    )
    raw = draft.to_storage()
    raw.update(screen="summary", history=["source_card", "edit_fields"])
    await state.update_data(
        source_draft=raw,
        last_card="Шаг 3 из 3\n\nTelegram-канал",
    )
    await state.set_state(SourceForm.summary)

    callback = FakeCallback("source:back")
    await source_wizard.go_back(callback, state)

    assert state.cleared is True
    assert callback.message.answers[-1][0].startswith("Telegram-канал")
    assert "Изменить" in labels(
        callback.message.answers[-1][1]["reply_markup"]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "active_state",
    [
        SourceForm.primary_input,
        SourceForm.value_review,
        SourceForm.options,
        SourceForm.field_input,
        SourceForm.summary,
    ],
)
async def test_inline_cancel_clears_every_source_wizard_state(active_state):
    from src.infoservice.bot.handlers.navigation import cancel_callback

    state = FakeState()
    draft = source_wizard.SourceDraft.new(str(uuid4()), "telegram")
    await source_wizard.store_draft(state, draft, active_state)
    callback = FakeCallback("cancel")

    await cancel_callback(callback, state)

    assert state.cleared is True
    assert "отменено" in callback.message.answers[-1][0].lower()


@pytest.mark.asyncio
async def test_back_from_first_input_returns_to_stable_catalog():
    state = FakeState()
    report_id = uuid4()
    draft = source_wizard.SourceDraft.new(str(report_id), "telegram")
    raw = draft.to_storage()
    raw.update(screen="primary", history=["catalog"])
    await source_wizard.store_draft(
        state, source_wizard.SourceDraft.from_storage(raw), SourceForm.primary_input
    )
    callback = FakeCallback("source:back")

    await source_wizard.go_back(callback, state)

    assert state.cleared is True
    assert labels(callback.message.answers[-1][1]["reply_markup"])[:4] == [
        "🟠 RSS / Atom",
        "🔵 Telegram-канал",
        "⚫ GitHub",
        "🟠 Hacker News",
    ]


@pytest.mark.asyncio
async def test_back_from_edit_options_returns_to_source_card():
    state = FakeState()
    source_id = uuid4()
    draft = source_wizard.SourceDraft.edit(
        str(source_id),
        "telegram",
        {"channel": "python_news", "fetch_limit": 20},
        enabled=False,
    )
    await source_wizard.store_draft(state, draft, SourceForm.options)
    callback = FakeCallback("source:back")

    await source_wizard.go_back(callback, state)

    assert state.cleared is True
    assert "приостановлен" in callback.message.answers[-1][0]
    assert "Изменить" in labels(callback.message.answers[-1][1]["reply_markup"])


@pytest.mark.asyncio
async def test_foreign_report_is_hidden_before_draft_creation(monkeypatch):
    class Repository:
        def __init__(self, _session):
            pass

        async def get_owned(self, *_args):
            from src.infoservice.errors import NotFound

            raise NotFound("Отчёт не найден")

    monkeypatch.setattr(source_wizard, "ReportRepository", Repository)
    state = FakeState()
    callback = FakeCallback(f"source:create:rss:{uuid4()}")

    await source_wizard.begin_create(
        callback, state, object(), SimpleNamespace(id=uuid4())
    )

    assert state.data == {}
    assert callback.answers[-1][1]["show_alert"] is True


def test_new_source_ui_contains_no_json_prompt():
    from src.infoservice.bot import messages_ru

    source_messages = [
        value
        for name, value in vars(messages_ru).items()
        if name.startswith("SOURCE_") and isinstance(value, str)
    ]
    assert all("json" not in text.lower() for text in source_messages)


@pytest.mark.asyncio
async def test_save_at_source_limit_keeps_draft_and_shows_limit(monkeypatch):
    report_id, user_id = uuid4(), uuid4()
    state = FakeState()
    draft = source_wizard.SourceDraft.new(
        str(report_id), "telegram"
    ).with_values(channel="python_news")
    await source_wizard.store_draft(state, draft, SourceForm.summary)

    class Repository:
        def __init__(self, _session):
            pass

        async def add_source(self, *_args):
            raise LimitExceeded("В отчёте может быть не более 30 источников")

    monkeypatch.setattr(source_wizard, "ReportRepository", Repository)
    callback = FakeCallback("source:save")

    await source_wizard.save_source(
        callback,
        state,
        object(),
        SimpleNamespace(id=user_id),
        SimpleNamespace(enable_twitter=False, enable_openbb=False),
    )

    assert state.cleared is False
    assert state.data["source_draft"]["report_id"] == str(report_id)
    assert callback.answers[-1] == (
        "В отчёте может быть не более 30 источников",
        {"show_alert": True},
    )
