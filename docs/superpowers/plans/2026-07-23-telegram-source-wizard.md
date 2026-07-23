# Telegram Source Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the bot-facing JSON source editor with a Russian, command-driven, step-by-step wizard for RSS, Telegram, GitHub, and Hacker News.

**Architecture:** Keep `SourceCatalog` and its Pydantic schemas as the persistence validation boundary. Add a pure source-form module that parses human input into the existing JSONB shape, a small navigation/command layer, and a dedicated FSM router that owns wizard transitions while the existing source router keeps list/toggle/delete CRUD.

**Tech Stack:** Python 3.11+, aiogram `>=3.25,<4` (currently locked to 3.30), Pydantic 2, SQLAlchemy 2 async, httpx, feedparser, pytest/pytest-asyncio.

## Global Constraints

- Only RSS/Atom, public Telegram channels, GitHub releases/user events, and Hacker News are creatable or editable in this iteration.
- Sources remain owned by one report; no reusable global source library is introduced.
- No bot screen asks for JSON or displays internal configuration field names.
- `SourceCatalog.validate()` remains the final validation step before every create or update.
- Existing JSONB shapes, worker contracts, Horizon adapters, and database schema remain unchanged.
- Existing beta/optional records remain viewable, toggleable, and deletable, but are not creatable or editable.
- The wizard uses the existing `MemoryStorage`; no Redis or persistent FSM dependency is added.
- Every text-input step shows the accepted value and an explicit `Далее →` callback before advancing.
- `/cancel` and the inline cancel action clear any active FSM draft without writing a partial source.
- User-facing copy is Russian and field errors include a reason plus a valid example.

---

## File Structure

### New files

- `src/infoservice/bot/commands.py` — canonical `BotCommand` list and bot command registration.
- `src/infoservice/bot/ui.py` — safe edit-or-answer helper used by callback-driven screens.
- `src/infoservice/bot/source_forms.py` — stable source form definitions, parsers, defaults, final validation, and human-readable cards.
- `src/infoservice/bot/handlers/navigation.py` — `/menu`, `/help`, `/settings`, `/cancel`, and matching main-menu callbacks.
- `src/infoservice/bot/handlers/source_wizard.py` — FSM orchestration for source creation and field-by-field editing.
- `tests/infoservice/bot/test_commands.py` — command registration and global navigation tests.
- `tests/infoservice/bot/test_source_forms.py` — pure parser/default/card tests.
- `tests/infoservice/bot/test_source_wizard.py` — FSM transition and persistence tests.

### Modified files

- `src/infoservice/bot/app.py` — include new routers and register commands before polling.
- `src/infoservice/bot/handlers/reports.py` — add `/reports` and `/newreport` entry points.
- `src/infoservice/bot/handlers/sources.py` — keep list/view/toggle/delete; delegate stable create/edit to the wizard and expose `/sources`.
- `src/infoservice/bot/keyboards.py` — hybrid main menu, navigation controls, stable catalog, source cards.
- `src/infoservice/bot/messages_ru.py` — command help, wizard prompts, errors, and summaries.
- `src/infoservice/bot/states.py` — explicit wizard states.
- `src/infoservice/sources/catalog.py` — public stable-capability selector.
- `tests/infoservice/bot/test_onboarding.py` — update expected main-menu callbacks.
- `tests/infoservice/bot/test_sources.py` — remove JSON creation expectations and retain CRUD/capability regression tests.
- `README_RU.md` — document commands and no-JSON stable-source setup.

---

### Task 1: Register Commands and Add Global Navigation

**Files:**
- Create: `src/infoservice/bot/commands.py`
- Create: `src/infoservice/bot/ui.py`
- Create: `src/infoservice/bot/handlers/navigation.py`
- Create: `tests/infoservice/bot/test_commands.py`
- Modify: `src/infoservice/bot/app.py:7-56`
- Modify: `src/infoservice/bot/handlers/start.py:5-28`
- Modify: `src/infoservice/bot/keyboards.py:1-18`
- Modify: `src/infoservice/bot/messages_ru.py:1-39`
- Modify: `tests/infoservice/bot/test_onboarding.py:14-24`

**Interfaces:**
- Produces: `BOT_COMMANDS: tuple[BotCommand, ...]`
- Produces: `async def configure_bot_commands(bot: Bot) -> None`
- Produces: `async def replace_or_answer(message: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> Message`
- Produces: `navigation.router`
- Consumes: existing `main_menu()`, `timezone_menu()`, and `FSMContext.clear()`.

- [ ] **Step 1: Write failing command registration tests**

```python
# tests/infoservice/bot/test_commands.py
from aiogram.types import BotCommand
import pytest

from src.infoservice.bot.commands import BOT_COMMANDS, configure_bot_commands


def test_bot_commands_have_expected_order_and_russian_descriptions():
    assert [item.command for item in BOT_COMMANDS] == [
        "start", "menu", "reports", "newreport", "sources",
        "settings", "help", "cancel",
    ]
    assert all(isinstance(item, BotCommand) for item in BOT_COMMANDS)
    assert all(item.description.strip() for item in BOT_COMMANDS)
    assert "отч" in BOT_COMMANDS[2].description.lower()


@pytest.mark.asyncio
async def test_configure_bot_commands_registers_default_scope():
    calls = []

    class Bot:
        async def set_my_commands(self, commands):
            calls.append(commands)
            return True

    await configure_bot_commands(Bot())

    assert calls == [list(BOT_COMMANDS)]
```

- [ ] **Step 2: Run the focused tests and confirm the missing module failure**

Run:

```bash
uv run pytest tests/infoservice/bot/test_commands.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'src.infoservice.bot.commands'`.

- [ ] **Step 3: Add the canonical command list and registration function**

```python
# src/infoservice/bot/commands.py
from aiogram import Bot
from aiogram.types import BotCommand


BOT_COMMANDS = (
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="menu", description="Открыть главное меню"),
    BotCommand(command="reports", description="Показать мои отчёты"),
    BotCommand(command="newreport", description="Создать новый отчёт"),
    BotCommand(command="sources", description="Управлять источниками"),
    BotCommand(command="settings", description="Настройки и ключ DeepSeek"),
    BotCommand(command="help", description="Команды и примеры"),
    BotCommand(command="cancel", description="Отменить текущее действие"),
)


async def configure_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(list(BOT_COMMANDS))
```

In `src/infoservice/bot/app.py`, call command registration before polling:

```python
from src.infoservice.bot.commands import configure_bot_commands

# inside run(), after Bot construction
bot = Bot(settings.telegram_bot_token.get_secret_value())
await configure_bot_commands(bot)
```

- [ ] **Step 4: Use the aiogram 3 command filter for `/start`**

In `handlers/start.py`, replace the text equality filter:

```python
from aiogram.filters import CommandStart


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.set_state(Onboarding.timezone)
    await message.answer(
        f"{WELCOME}\n{TIMEZONE_REQUEST}",
        reply_markup=timezone_menu(),
    )
```

- [ ] **Step 5: Add failing tests for `/menu`, `/help`, `/settings`, and `/cancel`**

```python
# append to tests/infoservice/bot/test_commands.py
from types import SimpleNamespace

from src.infoservice.bot.handlers.navigation import (
    cancel_action,
    help_command,
    menu_command,
    settings_command,
)


class FakeMessage:
    def __init__(self):
        self.answers = []

    async def answer(self, text, **kwargs):
        self.answers.append((text, kwargs))


class FakeState:
    def __init__(self, value="SourceForm:input"):
        self.value = value
        self.cleared = False

    async def get_state(self):
        return self.value

    async def clear(self):
        self.cleared = True
        self.value = None


@pytest.mark.asyncio
async def test_menu_clears_draft_and_shows_hybrid_keyboard():
    message, state = FakeMessage(), FakeState()
    await menu_command(message, state)
    assert state.cleared is True
    markup = message.answers[-1][1]["reply_markup"]
    labels = [button.text for row in markup.inline_keyboard for button in row]
    assert labels == ["📰 Мои отчёты", "➕ Новый отчёт", "🔑 DeepSeek", "⚙️ Настройки", "❓ Помощь"]


@pytest.mark.asyncio
async def test_help_lists_commands_and_stable_source_examples():
    message = FakeMessage()
    await help_command(message)
    text = message.answers[-1][0]
    assert "/reports" in text
    assert "/cancel" in text
    assert "@durov" in text
    assert "owner/repo" in text


@pytest.mark.asyncio
async def test_cancel_clears_active_state_and_returns_to_menu():
    message, state = FakeMessage(), FakeState()
    await cancel_action(message, state)
    assert state.cleared is True
    assert "отменено" in message.answers[-1][0].lower()


@pytest.mark.asyncio
async def test_settings_shows_timezone_and_deepseek_action():
    message = FakeMessage()
    await settings_command(message, SimpleNamespace(timezone="Europe/Moscow"))
    assert "Europe/Moscow" in message.answers[-1][0]
    labels = [
        button.text
        for row in message.answers[-1][1]["reply_markup"].inline_keyboard
        for button in row
    ]
    assert "🔑 DeepSeek" in labels
    assert "🌍 Часовой пояс" in labels
```

- [ ] **Step 6: Implement navigation messages, keyboards, and handlers**

Add these constants to `messages_ru.py`:

```python
COMMAND_HELP = """Команды InfoService:
/menu — главное меню
/reports — мои отчёты
/newreport — создать отчёт
/sources — источники выбранного отчёта
/settings — часовой пояс и DeepSeek
/help — помощь и примеры
/cancel — отменить текущее действие

Примеры источников:
Telegram: @durov
GitHub: owner/repo
RSS: https://example.com/feed.xml
Hacker News добавляется без адреса."""
SETTINGS_MENU = "Настройки\nЧасовой пояс: {timezone}"
NOTHING_TO_CANCEL = "Сейчас нет незавершённого действия."
ACTION_CANCELLED_MENU = "Действие отменено.\nГлавное меню"
```

Replace the main keyboard and add navigation keyboards in `keyboards.py`:

```python
MAIN_MENU_CALLBACKS = ("reports", "report:create", "llm", "settings", "help")


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📰 Мои отчёты", callback_data="reports"),
         InlineKeyboardButton(text="➕ Новый отчёт", callback_data="report:create")],
        [InlineKeyboardButton(text="🔑 DeepSeek", callback_data="llm"),
         InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])


def settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 DeepSeek", callback_data="llm")],
        [InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings:timezone")],
        [InlineKeyboardButton(text="‹ Главное меню", callback_data="menu")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="‹ Главное меню", callback_data="menu")]
    ])
```

Create `handlers/navigation.py` using aiogram 3 `Command` filters:

```python
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.infoservice.bot.keyboards import back_to_menu, main_menu, settings_menu, timezone_menu
from src.infoservice.bot.messages_ru import (
    ACTION_CANCELLED_MENU,
    COMMAND_HELP,
    MAIN_MENU,
    NOTHING_TO_CANCEL,
    SETTINGS_MENU,
    TIMEZONE_REQUEST,
)
from src.infoservice.bot.ui import replace_or_answer

router = Router(name="navigation")


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MAIN_MENU, reply_markup=main_menu())


@router.callback_query(F.data == "menu")
async def menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await replace_or_answer(callback.message, MAIN_MENU, main_menu())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(COMMAND_HELP, reply_markup=back_to_menu())


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await replace_or_answer(callback.message, COMMAND_HELP, back_to_menu())


@router.message(Command("settings"))
async def settings_command(message: Message, user) -> None:
    await message.answer(
        SETTINGS_MENU.format(timezone=user.timezone),
        reply_markup=settings_menu(),
    )


@router.callback_query(F.data == "settings")
async def settings_callback(callback: CallbackQuery, user) -> None:
    await callback.answer()
    await replace_or_answer(
        callback.message,
        SETTINGS_MENU.format(timezone=user.timezone),
        settings_menu(),
    )


@router.callback_query(F.data == "settings:timezone")
async def timezone_settings(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    from src.infoservice.bot.states import Onboarding
    await state.set_state(Onboarding.timezone)
    await replace_or_answer(callback.message, TIMEZONE_REQUEST, timezone_menu())


@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    text = ACTION_CANCELLED_MENU if current else NOTHING_TO_CANCEL
    await message.answer(text, reply_markup=main_menu())


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await replace_or_answer(callback.message, ACTION_CANCELLED_MENU, main_menu())
```

Create `ui.py`:

```python
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message


async def replace_or_answer(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    try:
        return await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        return await message.answer(text, reply_markup=reply_markup)
```

Include `navigation.router` first in `create_dispatcher()` so commands without state
filters are available during any FSM flow.

- [ ] **Step 7: Run command/navigation tests**

Run:

```bash
uv run pytest tests/infoservice/bot/test_commands.py tests/infoservice/bot/test_onboarding.py -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit the navigation slice**

```bash
git add src/infoservice/bot/commands.py src/infoservice/bot/ui.py \
  src/infoservice/bot/handlers/navigation.py src/infoservice/bot/handlers/start.py \
  src/infoservice/bot/app.py \
  src/infoservice/bot/keyboards.py src/infoservice/bot/messages_ru.py \
  tests/infoservice/bot/test_commands.py tests/infoservice/bot/test_onboarding.py
git commit -m "feat: add Telegram command navigation"
```

---

### Task 2: Build Pure Stable-Source Form Parsing

**Files:**
- Create: `src/infoservice/bot/source_forms.py`
- Create: `tests/infoservice/bot/test_source_forms.py`
- Modify: `src/infoservice/sources/catalog.py:38-73`

**Interfaces:**
- Produces: `STABLE_SOURCE_TYPES: tuple[str, ...]`
- Produces: `SourceDraft` with JSON-serializable `to_storage()` and `from_storage()`.
- Produces: `parse_primary(source_type: str, text: str, github_kind: str | None = None) -> dict[str, object]`
- Produces: `apply_field(draft: SourceDraft, field: str, text: str) -> SourceDraft`
- Produces: `async resolve_rss_name(url: str, client: httpx.AsyncClient | None = None) -> str`
- Produces: `validated_config(draft: SourceDraft, settings: Settings) -> dict[str, object]`
- Produces: `format_source_card(source_type: str, config: Mapping[str, object], enabled: bool = True) -> str`
- Produces: `SourceFieldError(field: str, reason: str, example: str)`
- Consumes: `SourceCatalog.validate()`, `safe_request()`, and existing strict source schemas.

- [ ] **Step 1: Write failing parser and catalog tests**

```python
# tests/infoservice/bot/test_source_forms.py
from types import SimpleNamespace

import pytest

from src.infoservice.bot.source_forms import (
    STABLE_SOURCE_TYPES,
    SourceDraft,
    SourceFieldError,
    apply_field,
    format_source_card,
    parse_primary,
    validated_config,
)
from src.infoservice.sources.catalog import SourceCatalog


def settings():
    return SimpleNamespace(enable_twitter=False, enable_openbb=False)


def test_catalog_exposes_exactly_four_stable_capabilities():
    assert [item.type for item in SourceCatalog.stable()] == list(STABLE_SOURCE_TYPES)


@pytest.mark.parametrize(
    ("raw", "channel"),
    [
        ("@python_news", "python_news"),
        ("https://t.me/python_news", "python_news"),
        ("python_news", "python_news"),
    ],
)
def test_parse_telegram_target(raw, channel):
    assert parse_primary("telegram", raw) == {"channel": channel}


def test_parse_rss_derives_safe_default_name():
    assert parse_primary("rss", "https://blog.example.com/feed.xml") == {
        "url": "https://blog.example.com/feed.xml",
        "name": "blog.example.com",
    }


def test_parse_github_repo_and_user_targets():
    assert parse_primary("github", "https://github.com/pallets/flask", "repo_releases") == {
        "type": "repo_releases",
        "owner": "pallets",
        "repo": "flask",
    }
    assert parse_primary("github", "https://github.com/octocat", "user_events") == {
        "type": "user_events",
        "username": "octocat",
    }


def test_hackernews_defaults_validate_through_source_catalog():
    draft = SourceDraft.new("report-id", "hackernews")
    assert validated_config(draft, settings())["fetch_top_stories"] == 30
    assert validated_config(draft, settings())["min_score"] == 100


def test_apply_field_returns_new_draft_and_normalizes_optional_category():
    draft = SourceDraft.new("report-id", "telegram").with_values(channel="python_news")
    updated = apply_field(draft, "category", "-")
    assert updated is not draft
    assert updated.values["category"] is None


def test_invalid_target_has_field_reason_and_example():
    with pytest.raises(SourceFieldError) as error:
        parse_primary("telegram", "https://t.me/+private")
    assert error.value.field == "channel"
    assert "@durov" in error.value.example


def test_human_card_contains_no_json_or_internal_field_names():
    text = format_source_card(
        "telegram",
        {"channel": "python_news", "fetch_limit": 20, "category": "Python"},
    )
    assert "@python_news" in text
    assert "20" in text
    assert "fetch_limit" not in text
    assert "{" not in text
```

- [ ] **Step 2: Run the source-form tests and confirm they fail**

Run:

```bash
uv run pytest tests/infoservice/bot/test_source_forms.py -v
```

Expected: collection fails because `source_forms` and `SourceCatalog.stable()` do not exist.

- [ ] **Step 3: Add the public stable catalog selector**

```python
# inside SourceCatalog in src/infoservice/sources/catalog.py
@classmethod
def stable(cls) -> list[SourceCapability]:
    stable_types = ("rss", "telegram", "github", "hackernews")
    capabilities = {
        capability.type: capability
        for capability in cls._CAPABILITIES
        if capability.stability == "stable"
    }
    return [capabilities[source_type] for source_type in stable_types]
```

- [ ] **Step 4: Implement source drafts, primary parsers, fields, and cards**

Create `source_forms.py` with these concrete types and defaults:

```python
from __future__ import annotations

from dataclasses import dataclass, field, replace
import re
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlsplit

import feedparser
import httpx

from src.infoservice.settings import Settings
from src.infoservice.sources.catalog import SourceCatalog, SourceValidationError
from src.url_security import UnsafeURLError, safe_request, validate_http_url

STABLE_SOURCE_TYPES = ("rss", "telegram", "github", "hackernews")
_TELEGRAM_USERNAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_]{4,31}$")
_GITHUB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULTS: Mapping[str, Mapping[str, Any]] = MappingProxyType({
    "rss": MappingProxyType({"enabled": True}),
    "telegram": MappingProxyType({"enabled": True, "fetch_limit": 20}),
    "github": MappingProxyType({"enabled": True}),
    "hackernews": MappingProxyType({
        "enabled": True,
        "fetch_top_stories": 30,
        "min_score": 100,
    }),
})


class SourceFieldError(ValueError):
    def __init__(self, field: str, reason: str, example: str) -> None:
        super().__init__(reason)
        self.field = field
        self.reason = reason
        self.example = example


@dataclass(frozen=True, slots=True)
class SourceDraft:
    report_id: str | None
    source_type: str
    source_id: str | None = None
    mode: str = "create"
    enabled: bool = True
    values: dict[str, Any] = field(default_factory=dict)
    current_field: str | None = None
    screen: str = "primary"
    history: tuple[str, ...] = ()

    @classmethod
    def new(cls, report_id: str, source_type: str) -> "SourceDraft":
        if source_type not in STABLE_SOURCE_TYPES:
            raise ValueError("unsupported stable source type")
        return cls(
            report_id=report_id,
            source_type=source_type,
            values=dict(DEFAULTS[source_type]),
        )

    @classmethod
    def edit(
        cls,
        source_id: str,
        source_type: str,
        values: Mapping[str, Any],
        enabled: bool,
    ) -> "SourceDraft":
        return cls(
            report_id=None,
            source_id=source_id,
            source_type=source_type,
            mode="edit",
            enabled=enabled,
            values=dict(values),
            screen="edit_fields",
            history=("source_card",),
        )

    def with_values(self, **values: Any) -> "SourceDraft":
        return replace(self, values={**self.values, **values})

    def to_storage(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "mode": self.mode,
            "enabled": self.enabled,
            "values": self.values,
            "current_field": self.current_field,
            "screen": self.screen,
            "history": list(self.history),
        }

    @classmethod
    def from_storage(cls, raw: Mapping[str, Any]) -> "SourceDraft":
        return cls(
            report_id=raw.get("report_id"),
            source_type=str(raw["source_type"]),
            source_id=raw.get("source_id"),
            mode=str(raw.get("mode", "create")),
            enabled=bool(raw.get("enabled", True)),
            values=dict(raw.get("values", {})),
            current_field=raw.get("current_field"),
            screen=str(raw.get("screen", "primary")),
            history=tuple(raw.get("history", ())),
        )


def _telegram_channel(text: str) -> str:
    value = text.strip()
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "t.me", "www.t.me", "telegram.me", "www.telegram.me",
        }:
            raise SourceFieldError("channel", "Нужна публичная ссылка t.me.", "@durov")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 1 or parts[0].startswith("+"):
            raise SourceFieldError("channel", "Приватные ссылки не поддерживаются.", "@durov")
        value = parts[0]
    value = value.removeprefix("@")
    if not _TELEGRAM_USERNAME.fullmatch(value):
        raise SourceFieldError(
            "channel",
            "Username должен содержать 5–32 буквы, цифры или подчёркивания.",
            "@durov",
        )
    return value


def _github_target(text: str, kind: str) -> dict[str, str]:
    value = text.strip().rstrip("/")
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "github.com", "www.github.com",
        }:
            raise SourceFieldError("target", "Нужна ссылка github.com.", "pallets/flask")
        value = parsed.path.strip("/")
    parts = value.split("/")
    if (
        kind == "repo_releases"
        and len(parts) == 2
        and all(_GITHUB_NAME.fullmatch(part) for part in parts)
    ):
        return {"type": kind, "owner": parts[0], "repo": parts[1]}
    if (
        kind == "user_events"
        and len(parts) == 1
        and _GITHUB_NAME.fullmatch(parts[0].removeprefix("@"))
    ):
        return {"type": kind, "username": parts[0].removeprefix("@")}
    example = "pallets/flask" if kind == "repo_releases" else "octocat"
    raise SourceFieldError("target", "Цель GitHub не соответствует выбранному типу.", example)


def parse_primary(
    source_type: str,
    text: str,
    github_kind: str | None = None,
) -> dict[str, Any]:
    value = text.strip()
    try:
        if source_type == "rss":
            validate_http_url(value)
            hostname = urlsplit(value).hostname or "RSS"
            return {"url": value, "name": hostname}
        if source_type == "telegram":
            return {"channel": _telegram_channel(value)}
        if source_type == "github":
            if github_kind not in {"repo_releases", "user_events"}:
                raise SourceFieldError("type", "Сначала выберите тип GitHub-источника.", "Релизы")
            return _github_target(value, github_kind)
        if source_type == "hackernews":
            return {}
    except UnsafeURLError as exc:
        raise SourceFieldError("url", "Нужна безопасная ссылка HTTP(S).", "https://example.com/feed.xml") from exc
    raise SourceFieldError("source_type", "Этот тип пока не поддерживается.", "RSS")


def apply_field(draft: SourceDraft, field_name: str, text: str) -> SourceDraft:
    value = text.strip()
    try:
        if field_name == "category":
            if value != "-" and len(value) > 255:
                raise ValueError
            parsed: Any = None if value == "-" else value
        elif field_name == "name":
            if not value or len(value) > 255:
                raise ValueError
            parsed = value
        elif field_name == "fetch_limit":
            parsed = int(value)
            if parsed not in {10, 20, 50}:
                raise ValueError
        elif field_name == "fetch_top_stories":
            parsed = int(value)
            if not 1 <= parsed <= 500:
                raise ValueError
        elif field_name == "min_score":
            parsed = int(value)
            if not 0 <= parsed <= 100_000:
                raise ValueError
        else:
            raise SourceFieldError(field_name, "Поле нельзя изменить.", "Выберите поле кнопкой")
    except ValueError as exc:
        examples = {
            "category": "Технологии",
            "name": "Python Blog",
            "fetch_limit": "20",
            "fetch_top_stories": "30",
            "min_score": "100",
        }
        raise SourceFieldError(field_name, "Значение вне допустимого диапазона.", examples[field_name]) from exc
    return draft.with_values(**{field_name: parsed})


async def resolve_rss_name(url: str, client: httpx.AsyncClient | None = None) -> str:
    fallback = urlsplit(url).hostname or "RSS"
    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=10)
    try:
        response = await safe_request(active_client, "GET", url, max_redirects=5)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        title = str(parsed.feed.get("title", "")).strip()
        return title[:255] or fallback
    except (httpx.HTTPError, UnsafeURLError, ValueError):
        return fallback
    finally:
        if owns_client:
            await active_client.aclose()


def validated_config(draft: SourceDraft, settings: Settings) -> dict[str, Any]:
    try:
        result = SourceCatalog.validate(draft.source_type, draft.values, settings)
    except SourceValidationError as exc:
        raise SourceFieldError(
            draft.current_field or "config",
            "Проверьте введённые значения.",
            "Вернитесь к полю и повторите ввод",
        ) from exc
    return result.model_dump(mode="json", exclude_none=True)


def format_source_card(
    source_type: str,
    config: Mapping[str, Any],
    enabled: bool = True,
) -> str:
    status = "включён" if enabled else "приостановлен"
    category = config.get("category") or "без категории"
    if source_type == "rss":
        details = f"Название: {config['name']}\nАдрес: {config['url']}"
        title = "RSS / Atom"
    elif source_type == "telegram":
        details = f"Канал: @{config['channel']}\nПроверять сообщений: {config.get('fetch_limit', 20)}"
        title = "Telegram-канал"
    elif source_type == "github":
        if config["type"] == "repo_releases":
            target = f"{config['owner']}/{config['repo']}"
            mode = "релизы репозитория"
        else:
            target = f"@{config['username']}"
            mode = "события пользователя"
        details = f"Режим: {mode}\nЦель: {target}"
        title = "GitHub"
    elif source_type == "hackernews":
        details = (
            f"Проверять публикаций: {config.get('fetch_top_stories', 30)}\n"
            f"Минимальный рейтинг: {config.get('min_score', 100)}"
        )
        title = "Hacker News"
    else:
        return f"Источник: {source_type}\nСостояние: {status}"
    return f"{title}\n{details}\nКатегория: {category}\nСостояние: {status}"
```

- [ ] **Step 5: Add and run RSS title-discovery tests**

```python
# append to tests/infoservice/bot/test_source_forms.py
import httpx
from types import SimpleNamespace

from src.infoservice.bot.source_forms import resolve_rss_name


@pytest.mark.asyncio
async def test_rss_name_uses_feed_title(monkeypatch):
    async def safe_request(*_args, **_kwargs):
        return SimpleNamespace(
            content=b"<rss><channel><title>Python Weekly</title></channel></rss>",
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr("src.infoservice.bot.source_forms.safe_request", safe_request)
    assert await resolve_rss_name("https://example.com/feed.xml", SimpleNamespace()) == "Python Weekly"


@pytest.mark.asyncio
async def test_rss_name_falls_back_to_hostname_on_fetch_failure(monkeypatch):
    async def safe_request(*_args, **_kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr("src.infoservice.bot.source_forms.safe_request", safe_request)
    assert await resolve_rss_name("https://blog.example.com/feed.xml", SimpleNamespace()) == "blog.example.com"
```

Run:

```bash
uv run pytest tests/infoservice/bot/test_source_forms.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit the pure form domain**

```bash
git add src/infoservice/bot/source_forms.py src/infoservice/sources/catalog.py \
  tests/infoservice/bot/test_source_forms.py
git commit -m "feat: parse stable source form input"
```

---

### Task 3: Add Wizard States and Keyboards

**Files:**
- Modify: `src/infoservice/bot/states.py:33-35`
- Modify: `src/infoservice/bot/keyboards.py:54-68`
- Modify: `src/infoservice/bot/messages_ru.py`
- Create: `tests/infoservice/bot/test_source_wizard.py`

**Interfaces:**
- Produces: `SourceForm.primary_input`, `value_review`, `options`, `field_input`, `summary`, `delete_confirmation`.
- Produces: `source_catalog_menu(report_id: str)`.
- Produces: `primary_input_menu()`, `accepted_value_menu()`, `source_options_menu()`, `field_menu(source_type: str)`, `summary_menu()`, `source_menu(source_id: str, enabled: bool, editable: bool)`.
- Consumes: `STABLE_SOURCE_TYPES` and stable form field names from Task 2.

- [ ] **Step 1: Write failing state and keyboard contract tests**

```python
# tests/infoservice/bot/test_source_wizard.py
from src.infoservice.bot.keyboards import (
    accepted_value_menu,
    field_menu,
    primary_input_menu,
    source_catalog_menu,
    source_menu,
    source_options_menu,
    summary_menu,
)
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
```

- [ ] **Step 2: Run tests and confirm missing states/signatures**

Run:

```bash
uv run pytest tests/infoservice/bot/test_source_wizard.py -v
```

Expected: failures for missing state attributes and keyboard functions.

- [ ] **Step 3: Replace the JSON form state with explicit wizard states**

```python
class SourceForm(StatesGroup):
    primary_input = State()
    value_review = State()
    options = State()
    field_input = State()
    summary = State()
    delete_confirmation = State()
```

- [ ] **Step 4: Implement stable-only wizard keyboards**

Use these callback IDs in `keyboards.py`:

```python
def source_catalog_menu(report_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟠 RSS / Atom", callback_data=f"source:create:rss:{report_id}")],
        [InlineKeyboardButton(text="🔵 Telegram-канал", callback_data=f"source:create:telegram:{report_id}")],
        [InlineKeyboardButton(text="⚫ GitHub", callback_data=f"source:create:github:{report_id}")],
        [InlineKeyboardButton(text="🟠 Hacker News", callback_data=f"source:create:hackernews:{report_id}")],
        [InlineKeyboardButton(text="‹ Назад", callback_data=f"source:list:{report_id}")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])


def primary_input_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
        InlineKeyboardButton(text="Отмена", callback_data="cancel"),
    ]])


def accepted_value_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Далее →", callback_data="source:next")],
        [InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
         InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])


def source_options_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Далее →", callback_data="source:summary")],
        [InlineKeyboardButton(text="⚙️ Дополнительные настройки", callback_data="source:advanced")],
        [InlineKeyboardButton(text="Значения по умолчанию", callback_data="source:summary")],
        [InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
         InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])


def field_menu(source_type: str) -> InlineKeyboardMarkup:
    fields = {
        "rss": [("Название", "name"), ("Категория", "category")],
        "telegram": [("Категория", "category"), ("Количество сообщений", "fetch_limit")],
        "github": [("Категория", "category")],
        "hackernews": [
            ("Количество публикаций", "fetch_top_stories"),
            ("Минимальный рейтинг", "min_score"),
            ("Категория", "category"),
        ],
    }[source_type]
    rows = [[InlineKeyboardButton(text=label, callback_data=f"source:field:{name}")]
            for label, name in fields]
    rows.extend([
        [InlineKeyboardButton(text="Готово", callback_data="source:summary")],
        [InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
         InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def summary_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранить источник", callback_data="source:save"),
         InlineKeyboardButton(text="✏️ Изменить", callback_data="source:advanced")],
        [InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
         InlineKeyboardButton(text="Отмена", callback_data="cancel")],
    ])
```

Change `source_menu` to accept an explicit editability flag:

```python
def source_menu(source_id: str, enabled: bool, editable: bool = True) -> InlineKeyboardMarkup:
    toggle = "disable" if enabled else "enable"
    label = "Отключить" if enabled else "Включить"
    rows = []
    if editable:
        rows.append([InlineKeyboardButton(
            text="Изменить",
            callback_data=f"source:edit:{source_id}",
        )])
    rows.extend([
        [InlineKeyboardButton(text=label, callback_data=f"source:{toggle}:{source_id}")],
        [InlineKeyboardButton(text="Удалить", callback_data=f"source:delete:{source_id}")],
        [InlineKeyboardButton(text="‹ Главное меню", callback_data="menu")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
```

- [ ] **Step 5: Add wizard copy and run keyboard tests**

Add Russian prompt templates:

```python
SOURCE_TYPE_REQUEST = "Выберите тип источника."
SOURCE_PRIMARY_PROMPTS = {
    "rss": "Отправьте ссылку на RSS/Atom-ленту.\nПример: https://example.com/feed.xml",
    "telegram": "Отправьте @username или публичную ссылку t.me.\nПример: @durov",
    "github": "Отправьте цель GitHub.\nПример: pallets/flask",
}
SOURCE_VALUE_ACCEPTED = "Принято: {value}"
SOURCE_OPTIONS = "Можно продолжить со значениями по умолчанию или изменить дополнительные настройки."
SOURCE_FIELD_PROMPTS = {
    "name": "Введите отображаемое название.\nПример: Python Weekly",
    "category": "Введите категорию или «-», чтобы пропустить.\nПример: Технологии",
    "fetch_limit": "Выберите 10, 20 или 50 сообщений.",
    "fetch_top_stories": "Введите количество публикаций от 1 до 500.\nПример: 30",
    "min_score": "Введите минимальный рейтинг от 0 до 100000.\nПример: 100",
}
SOURCE_FIELD_ERROR = "Не удалось принять поле «{field}»: {reason}\nПример: {example}"
```

Run:

```bash
uv run pytest tests/infoservice/bot/test_source_wizard.py -v
```

Expected: all keyboard/state contract tests pass.

- [ ] **Step 6: Commit wizard presentation contracts**

```bash
git add src/infoservice/bot/states.py src/infoservice/bot/keyboards.py \
  src/infoservice/bot/messages_ru.py tests/infoservice/bot/test_source_wizard.py
git commit -m "feat: add stable source wizard controls"
```

---

### Task 4: Implement Creation Flow, Back Navigation, and Persistence

**Files:**
- Create: `src/infoservice/bot/handlers/source_wizard.py`
- Modify: `src/infoservice/bot/app.py:11-36`
- Modify: `src/infoservice/bot/handlers/sources.py:1-130`
- Modify: `tests/infoservice/bot/test_source_wizard.py`
- Modify: `tests/infoservice/bot/test_sources.py`

**Interfaces:**
- Produces: `source_wizard.router`.
- Produces: `async load_draft(state: FSMContext) -> SourceDraft`.
- Produces: `async store_draft(state: FSMContext, draft: SourceDraft, next_state: State) -> None`.
- Produces: `step_label(draft: SourceDraft, screen: str) -> str`.
- Produces: create callbacks `source:create:*`, `source:next`, `source:advanced`, `source:summary`, `source:back`, `source:save`.
- Consumes: Task 2 parsing/validation and Task 3 keyboard contracts.
- Persists with `ReportRepository.add_source(report_id, user.id, CreateSource(...))`.

- [ ] **Step 1: Add failing happy-path tests for all four types**

```python
# append to tests/infoservice/bot/test_source_wizard.py
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.infoservice.bot.handlers import source_wizard
from src.infoservice.bot.states import SourceForm


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
    await source_wizard.begin_create(start, state, object(), SimpleNamespace(id=uuid4()))

    if github_kind:
        await source_wizard.choose_github_kind(
            FakeCallback(f"source:github-kind:{github_kind}"), state
        )
    if primary is not None:
        await source_wizard.receive_primary(FakeMessage(primary), state)
        assert state.value == SourceForm.value_review
        await source_wizard.accept_primary(FakeCallback("source:next"), state)
    await source_wizard.show_summary(
        FakeCallback("source:summary"), state, SimpleNamespace(enable_twitter=False, enable_openbb=False)
    )

    assert state.value == SourceForm.summary
    assert "{" not in state.data["last_card"]
    expected_progress = "Шаг 2 из 2" if source_type == "hackernews" else "Шаг 3 из 3"
    assert state.data["last_card"].startswith(expected_progress)
```

- [ ] **Step 2: Run happy-path tests and verify handler module failure**

Run:

```bash
uv run pytest tests/infoservice/bot/test_source_wizard.py -k creation_flow -v
```

Expected: import failure for `handlers.source_wizard`.

- [ ] **Step 3: Implement draft loading, storing, begin, primary input, and explicit next**

Create `handlers/source_wizard.py` with these helpers and handlers:

```python
from __future__ import annotations

from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message

from src.infoservice.bot.keyboards import (
    accepted_value_menu,
    field_menu,
    primary_input_menu,
    source_options_menu,
    summary_menu,
)
from src.infoservice.bot.messages_ru import (
    SOURCE_FIELD_ERROR,
    SOURCE_OPTIONS,
    SOURCE_PRIMARY_PROMPTS,
    SOURCE_VALUE_ACCEPTED,
)
from src.infoservice.bot.source_forms import (
    SourceDraft,
    SourceFieldError,
    format_source_card,
    parse_primary,
    resolve_rss_name,
    validated_config,
)
from src.infoservice.bot.states import SourceForm
from src.infoservice.bot.ui import replace_or_answer
from src.infoservice.db.repositories.reports import CreateSource, ReportRepository
from src.infoservice.errors import LimitExceeded, NotFound

router = Router(name="source_wizard")


def _uuid(value: str | None) -> UUID | None:
    try:
        return UUID(value or "")
    except ValueError:
        return None


async def load_draft(state: FSMContext) -> SourceDraft:
    raw = (await state.get_data()).get("source_draft")
    if not isinstance(raw, dict):
        raise ValueError("source draft is missing")
    return SourceDraft.from_storage(raw)


async def store_draft(
    state: FSMContext,
    draft: SourceDraft,
    next_state: State,
) -> None:
    await state.update_data(source_draft=draft.to_storage())
    await state.set_state(next_state)


def step_label(draft: SourceDraft, screen: str) -> str:
    if draft.source_type == "hackernews":
        current = {"options": 1, "advanced": 1, "summary": 2}[screen]
        return f"Шаг {current} из 2"
    current = {
        "primary": 1,
        "value_review": 1,
        "options": 2,
        "advanced": 2,
        "field_input": 2,
        "field_review": 2,
        "summary": 3,
    }[screen]
    return f"Шаг {current} из 3"


@router.callback_query(F.data.startswith("source:create:"))
async def begin_create(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 4:
        await callback.answer("Источник не найден", show_alert=True)
        return
    source_type, report_text = parts[2], parts[3]
    report_id = _uuid(report_text)
    try:
        if report_id is None:
            raise NotFound("Отчёт не найден")
        await ReportRepository(session).get_owned(report_id, user.id)
        draft = SourceDraft.new(str(report_id), source_type)
    except (NotFound, ValueError):
        await callback.answer("Отчёт или источник не найден", show_alert=True)
        return
    await callback.answer()
    if source_type == "hackernews":
        draft = SourceDraft.from_storage({
            **draft.to_storage(),
            "screen": "options",
            "history": ["catalog"],
        })
        await store_draft(state, draft, SourceForm.options)
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'options')}\n{SOURCE_OPTIONS}",
            source_options_menu(),
        )
        return
    if source_type == "github":
        draft = SourceDraft.from_storage({
            **draft.to_storage(),
            "screen": "github_kind",
            "history": ["catalog"],
        })
        await store_draft(state, draft, SourceForm.primary_input)
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Релизы репозитория", callback_data="source:github-kind:repo_releases")],
            [InlineKeyboardButton(text="События пользователя", callback_data="source:github-kind:user_events")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ])
        await replace_or_answer(callback.message, "Что отслеживать в GitHub?", markup)
        return
    draft = SourceDraft.from_storage({
        **draft.to_storage(),
        "screen": "primary",
        "history": ["catalog"],
    })
    await store_draft(state, draft, SourceForm.primary_input)
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'primary')}\n{SOURCE_PRIMARY_PROMPTS[source_type]}",
        primary_input_menu(),
    )


@router.callback_query(F.data.startswith("source:github-kind:"))
async def choose_github_kind(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await load_draft(state)
    kind = (callback.data or "").rsplit(":", 1)[-1]
    if draft.source_type != "github" or kind not in {"repo_releases", "user_events"}:
        await callback.answer("Некорректный режим GitHub", show_alert=True)
        return
    draft = draft.with_values(type=kind)
    draft = SourceDraft.from_storage({
        **draft.to_storage(),
        "screen": "primary",
        "history": [*draft.history, "github_kind"],
    })
    await store_draft(state, draft, SourceForm.primary_input)
    await callback.answer()
    example = "pallets/flask" if kind == "repo_releases" else "octocat"
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'primary')}\nОтправьте цель GitHub.\nПример: {example}",
        primary_input_menu(),
    )


@router.message(SourceForm.primary_input, F.text)
async def receive_primary(message: Message, state: FSMContext) -> None:
    draft = await load_draft(state)
    try:
        values = parse_primary(
            draft.source_type,
            message.text,
            str(draft.values.get("type")) if draft.source_type == "github" else None,
        )
        if draft.source_type == "rss":
            values["name"] = await resolve_rss_name(str(values["url"]))
        draft = draft.with_values(**values)
    except SourceFieldError as exc:
        await message.answer(SOURCE_FIELD_ERROR.format(
            field=exc.field, reason=exc.reason, example=exc.example
        ))
        return
    draft = SourceDraft.from_storage({
        **draft.to_storage(),
        "screen": "value_review",
        "history": [*draft.history, "primary"],
    })
    await store_draft(state, draft, SourceForm.value_review)
    accepted = values.get("url") or values.get("channel") or values.get("repo") or values.get("username")
    await message.answer(
        f"{step_label(draft, 'value_review')}\n"
        f"{SOURCE_VALUE_ACCEPTED.format(value=accepted)}",
        reply_markup=accepted_value_menu(),
    )


@router.callback_query(SourceForm.value_review, F.data == "source:next")
async def accept_primary(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await load_draft(state)
    draft = SourceDraft.from_storage({
        **draft.to_storage(),
        "screen": "options",
        "history": [*draft.history, "value_review"],
    })
    await store_draft(state, draft, SourceForm.options)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'options')}\n{SOURCE_OPTIONS}",
        source_options_menu(),
    )
```

- [ ] **Step 4: Add failing back, validation-error, and save tests**

```python
# append to tests/infoservice/bot/test_source_wizard.py
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
    draft = source_wizard.SourceDraft.new(str(uuid4()), "telegram").with_values(channel="python_news")
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
    draft = source_wizard.SourceDraft.new(str(report_id), "telegram").with_values(
        channel="python_news"
    )
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
```

- [ ] **Step 5: Implement options, summary, back, and create persistence**

Add to `source_wizard.py`:

```python
@router.callback_query(SourceForm.options, F.data == "source:advanced")
@router.callback_query(SourceForm.summary, F.data == "source:advanced")
async def show_advanced(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await load_draft(state)
    raw = draft.to_storage()
    raw.update(screen="advanced", history=[*draft.history, draft.screen])
    draft = SourceDraft.from_storage(raw)
    await store_draft(state, draft, SourceForm.options)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'advanced')}\nВыберите параметр.",
        field_menu(draft.source_type),
    )


@router.callback_query(F.data == "source:summary")
async def show_summary(callback: CallbackQuery, state: FSMContext, settings) -> None:
    draft = await load_draft(state)
    try:
        config = validated_config(draft, settings)
    except SourceFieldError as exc:
        await callback.answer(
            SOURCE_FIELD_ERROR.format(field=exc.field, reason=exc.reason, example=exc.example),
            show_alert=True,
        )
        return
    raw = draft.to_storage()
    raw.update(screen="summary", history=[*draft.history, draft.screen])
    draft = SourceDraft.from_storage(raw)
    card = (
        f"{step_label(draft, 'summary')}\n\n"
        f"{format_source_card(draft.source_type, config)}"
    )
    await state.update_data(source_draft=draft.to_storage(), last_card=card)
    await state.set_state(SourceForm.summary)
    await callback.answer()
    await replace_or_answer(callback.message, card, summary_menu())


@router.callback_query(F.data == "source:back")
async def go_back(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await load_draft(state)
    history = list(draft.history)
    previous = history.pop() if history else "catalog"
    raw = draft.to_storage()
    raw.update(screen=previous, history=history)
    draft = SourceDraft.from_storage(raw)
    await callback.answer()
    if previous == "catalog":
        report_id = draft.report_id
        await state.clear()
        if report_id is None:
            await replace_or_answer(callback.message, "Выберите отчёт заново.")
        else:
            from src.infoservice.bot.keyboards import source_catalog_menu
            await replace_or_answer(
                callback.message,
                "Выберите тип источника.",
                source_catalog_menu(report_id),
            )
    elif previous == "source_card":
        await state.clear()
        from src.infoservice.bot.keyboards import source_menu
        if draft.source_id is None:
            await replace_or_answer(callback.message, "Источник не найден.")
        else:
            await replace_or_answer(
                callback.message,
                format_source_card(draft.source_type, draft.values, draft.enabled),
                source_menu(draft.source_id, draft.enabled, editable=True),
            )
    elif previous == "github_kind":
        await store_draft(state, draft, SourceForm.primary_input)
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Релизы репозитория", callback_data="source:github-kind:repo_releases")],
            [InlineKeyboardButton(text="События пользователя", callback_data="source:github-kind:user_events")],
            [InlineKeyboardButton(text="‹ Назад", callback_data="source:back"),
             InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ])
        await replace_or_answer(callback.message, "Что отслеживать в GitHub?", markup)
    elif previous == "value_review":
        await store_draft(state, draft, SourceForm.value_review)
        value = (
            draft.values.get("url")
            or draft.values.get("channel")
            or draft.values.get("repo")
            or draft.values.get("username")
        )
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'value_review')}\n"
            f"{SOURCE_VALUE_ACCEPTED.format(value=value)}",
            accepted_value_menu(),
        )
    elif previous in {"options", "advanced"}:
        await store_draft(state, draft, SourceForm.options)
        markup = field_menu(draft.source_type) if previous == "advanced" else source_options_menu()
        text = (
            f"{step_label(draft, 'advanced')}\nВыберите параметр."
            if previous == "advanced"
            else f"{step_label(draft, 'options')}\n{SOURCE_OPTIONS}"
        )
        await replace_or_answer(callback.message, text, markup)
    else:
        await store_draft(state, draft, SourceForm.primary_input)
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'primary')}\n"
            f"{SOURCE_PRIMARY_PROMPTS.get(draft.source_type, 'Выберите тип источника заново.')}",
            primary_input_menu(),
        )


@router.callback_query(SourceForm.summary, F.data == "source:save")
async def save_source(callback: CallbackQuery, state: FSMContext, session, user, settings) -> None:
    draft = await load_draft(state)
    try:
        config = validated_config(draft, settings)
        display_name = str(
            config.get("name")
            or config.get("channel")
            or config.get("username")
            or (
                f"{config.get('owner')}/{config.get('repo')}"
                if config.get("owner") and config.get("repo")
                else "Hacker News"
            )
        )
        repository = ReportRepository(session)
        if draft.mode == "edit":
            source_id = _uuid(draft.source_id)
            if source_id is None:
                raise NotFound("Источник не найден")
            source = await repository.update_source(
                source_id,
                user.id,
                config=config,
                display_name=display_name,
            )
            text = "Источник обновлён."
        else:
            report_id = _uuid(draft.report_id)
            if report_id is None:
                raise NotFound("Отчёт не найден")
            source = await repository.add_source(
                report_id,
                user.id,
                CreateSource(
                    source_type=draft.source_type,
                    display_name=display_name,
                    config=config,
                ),
            )
            text = "Источник добавлен."
    except LimitExceeded as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except (NotFound, SourceFieldError):
        await callback.answer("Источник или отчёт не найден", show_alert=True)
        return
    await state.clear()
    await callback.answer()
    from src.infoservice.bot.keyboards import source_menu
    await replace_or_answer(
        callback.message,
        text,
        source_menu(str(source.id), source.enabled, editable=True),
    )
```

- [ ] **Step 6: Move stable create ownership from `sources.py` and include the router**

In `sources.py`:

- remove `json`, `SOURCE_CONFIG_REQUEST`, `SourceCatalog` create validation,
  `begin_source_form()`, `receive_source_config()`, and JSON-based `edit_source()`;
- remove obsolete `SOURCE_CONFIG_REQUEST` and `SOURCE_OPTIONAL_PREREQUISITE`
  constants from `messages_ru.py`;
- remove `available_source_labels()` and replace its old optional-source tests
  with the stable-catalog contract from Task 3;
- call `source_catalog_menu(str(report_id))` without passing capabilities;
- make `open_catalog()` call `list_sources(report_id, user.id)` and show the
  repository's 30-source limit as an alert before starting a new draft;
- keep `list_sources`, `view_source`, toggle, delete, and owner checks;
- render `view_source` with `format_source_card()` when `source_type` is stable;
- pass `editable=source.source_type in STABLE_SOURCE_TYPES` to `source_menu()`.
- use `replace_or_answer()` for callback-driven list, catalog, source-card,
  toggle, and delete-result screens.

In `app.py`, include `source_wizard_router` before `sources_router`:

```python
from src.infoservice.bot.handlers.source_wizard import router as source_wizard_router

dispatcher.include_routers(
    navigation_router,
    start_router,
    credentials_router,
    reports_router,
    rules_router,
    schedules_router,
    source_wizard_router,
    sources_router,
)
```

- [ ] **Step 7: Run creation and source CRUD tests**

Run:

```bash
uv run pytest tests/infoservice/bot/test_source_wizard.py \
  tests/infoservice/bot/test_sources.py -v
```

Expected: all tests pass and no test serializes source input with `json.dumps`.

- [ ] **Step 8: Commit the source creation flow**

```bash
git add src/infoservice/bot/handlers/source_wizard.py \
  src/infoservice/bot/handlers/sources.py src/infoservice/bot/app.py \
  tests/infoservice/bot/test_source_wizard.py tests/infoservice/bot/test_sources.py
git commit -m "feat: add conversational source creation"
```

---

### Task 5: Add Advanced Field Editing and Command Entry Points

**Files:**
- Modify: `src/infoservice/bot/handlers/source_wizard.py`
- Modify: `src/infoservice/bot/handlers/sources.py`
- Modify: `src/infoservice/bot/handlers/reports.py`
- Modify: `src/infoservice/bot/keyboards.py`
- Modify: `tests/infoservice/bot/test_source_wizard.py`
- Modify: `tests/infoservice/bot/test_reports.py`

**Interfaces:**
- Produces: callback `source:field:<name>` plus `SourceForm.field_input` handler.
- Produces: stable `source:edit:<uuid>` draft initialization.
- Produces: `/reports`, `/newreport`, and `/sources` command handlers.
- Consumes: `apply_field()`, `format_source_card()`, owner-scoped repository methods.

- [ ] **Step 1: Write failing advanced-field and single-field edit tests**

```python
# append to tests/infoservice/bot/test_source_wizard.py
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
    assert "Далее →" in [
        button.text
        for row in message.answers[-1][1]["reply_markup"].inline_keyboard
        for button in row
    ]


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
```

- [ ] **Step 2: Run focused tests and confirm missing handlers**

Run:

```bash
uv run pytest tests/infoservice/bot/test_source_wizard.py \
  -k "field or edit_stable" -v
```

Expected: failures for missing `receive_field()` and `begin_edit()`.

- [ ] **Step 3: Implement field selection, validation, and explicit next**

Add to `source_wizard.py`:

```python
from src.infoservice.bot.messages_ru import SOURCE_FIELD_PROMPTS
from src.infoservice.bot.source_forms import STABLE_SOURCE_TYPES, apply_field


@router.callback_query(F.data.startswith("source:field:"))
async def choose_field(callback: CallbackQuery, state: FSMContext) -> None:
    draft = await load_draft(state)
    field_name = (callback.data or "").rsplit(":", 1)[-1]
    if field_name not in SOURCE_FIELD_PROMPTS:
        await callback.answer("Поле недоступно", show_alert=True)
        return
    raw = draft.to_storage()
    raw.update(
        current_field=field_name,
        screen="field_input",
        history=[*draft.history, "advanced"],
    )
    await store_draft(state, SourceDraft.from_storage(raw), SourceForm.field_input)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        f"{step_label(draft, 'field_input')}\n{SOURCE_FIELD_PROMPTS[field_name]}",
    )


@router.message(SourceForm.field_input, F.text)
async def receive_field(message: Message, state: FSMContext) -> None:
    draft = await load_draft(state)
    if draft.current_field is None:
        await message.answer("Выберите поле заново.")
        return
    try:
        draft = apply_field(draft, draft.current_field, message.text)
    except SourceFieldError as exc:
        await message.answer(SOURCE_FIELD_ERROR.format(
            field=exc.field, reason=exc.reason, example=exc.example
        ))
        return
    raw = draft.to_storage()
    raw.update(screen="field_review", history=[*draft.history, "field_input"])
    draft = SourceDraft.from_storage(raw)
    await store_draft(state, draft, SourceForm.value_review)
    await message.answer(
        f"{step_label(draft, 'field_review')}\n"
        f"{SOURCE_VALUE_ACCEPTED.format(value=message.text.strip())}",
        reply_markup=accepted_value_menu(),
    )
```

Update `accept_primary()` so a reviewed advanced field returns to `field_menu`
instead of the general options screen:

```python
    if draft.current_field is not None and draft.screen == "field_review":
        history = list(draft.history)
        if history[-2:] == ["advanced", "field_input"]:
            history = history[:-2]
        raw = draft.to_storage()
        raw.update(screen="advanced", current_field=None, history=history)
        draft = SourceDraft.from_storage(raw)
        await store_draft(state, draft, SourceForm.options)
        await callback.answer()
        await replace_or_answer(
            callback.message,
            f"{step_label(draft, 'advanced')}\n"
            "Параметр сохранён. Можно изменить ещё один.",
            field_menu(draft.source_type),
        )
        return
```

- [ ] **Step 4: Implement stable edit initialization and beta edit refusal**

```python
@router.callback_query(F.data.startswith("source:edit:"))
async def begin_edit(callback: CallbackQuery, state: FSMContext, session, user) -> None:
    source_id = _uuid((callback.data or "").rsplit(":", 1)[-1])
    try:
        if source_id is None:
            raise NotFound("Источник не найден")
        source = await ReportRepository(session).get_source_owned(source_id, user.id)
    except NotFound:
        await callback.answer("Источник не найден", show_alert=True)
        return
    if source.source_type not in STABLE_SOURCE_TYPES:
        await callback.answer(
            "Редактирование этого типа пока недоступно. Его можно отключить или удалить.",
            show_alert=True,
        )
        return
    draft = SourceDraft.edit(
        str(source.id),
        source.source_type,
        source.config,
        source.enabled,
    )
    await store_draft(state, draft, SourceForm.options)
    await callback.answer()
    await replace_or_answer(
        callback.message,
        format_source_card(source.source_type, source.config, source.enabled),
        field_menu(source.source_type),
    )
```

- [ ] **Step 5: Add `/reports`, `/newreport`, and `/sources` handler tests**

```python
# append to tests/infoservice/bot/test_reports.py
from src.infoservice.bot.handlers.reports import reports_command, new_report_command


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
    await new_report_command(Message(), state)
    assert state.value == CreateReport.name
    assert "название" in replies[-1][0].lower()
```

Add a `/sources` test to `test_sources.py` that returns two owned reports and
asserts buttons point to `source:list:<report-id>`.

- [ ] **Step 6: Implement command entry points without calling callback handlers**

In `reports.py`, extract a shared report-list builder and add `Command` handlers:

```python
from aiogram.filters import Command


def report_list_markup(reports) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Создать отчёт", callback_data="report:create")]]
    rows.extend([
        [InlineKeyboardButton(text=report.name, callback_data=f"report:view:{report.id}")]
        for report in reports
    ])
    rows.append([InlineKeyboardButton(text="‹ Главное меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("reports"))
async def reports_command(message: Message, state: FSMContext, session, user) -> None:
    await state.clear()
    reports = await ReportRepository(session).list_owned(user.id)
    text = REPORTS_MENU if reports else f"{REPORTS_MENU}\nСоздайте первый отчёт."
    await message.answer(text, reply_markup=report_list_markup(reports))


@router.message(Command("newreport"))
async def new_report_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CreateReport.name)
    await message.answer(REPORT_NAME_REQUEST)
```

Use `report_list_markup()` from the existing callback handler.

In `sources.py`:

```python
from aiogram.filters import Command


@router.message(Command("sources"))
async def sources_command(message: Message, state: FSMContext, session, user) -> None:
    await state.clear()
    reports = await ReportRepository(session).list_owned(user.id)
    if not reports:
        await message.answer(
            "Сначала создайте отчёт.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="➕ Новый отчёт", callback_data="report:create")
            ]]),
        )
        return
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=report.name,
            callback_data=f"source:list:{report.id}",
        )]
        for report in reports
    ])
    await message.answer("Выберите отчёт.", reply_markup=markup)
```

- [ ] **Step 7: Run all bot tests**

Run:

```bash
uv run pytest tests/infoservice/bot -v
```

Expected: all bot tests pass; no screen or assertion contains
`Отправьте JSON-конфигурацию`.

- [ ] **Step 8: Commit advanced editing and command entry points**

```bash
git add src/infoservice/bot/handlers/source_wizard.py \
  src/infoservice/bot/handlers/sources.py src/infoservice/bot/handlers/reports.py \
  src/infoservice/bot/keyboards.py tests/infoservice/bot/test_source_wizard.py \
  tests/infoservice/bot/test_sources.py tests/infoservice/bot/test_reports.py
git commit -m "feat: add source field editing and shortcuts"
```

---

### Task 6: Complete Regression Coverage and User Documentation

**Files:**
- Modify: `tests/infoservice/bot/test_commands.py`
- Modify: `tests/infoservice/bot/test_source_wizard.py`
- Modify: `tests/infoservice/bot/test_sources.py`
- Modify: `README_RU.md`

**Interfaces:**
- Consumes all public contracts from Tasks 1–5.
- Produces no new runtime API.

- [ ] **Step 1: Add regression tests for cancellation, ownership, limits, and forbidden JSON UX**

```python
# append to tests/infoservice/bot/test_source_wizard.py
@pytest.mark.asyncio
@pytest.mark.parametrize("active_state", [
    SourceForm.primary_input,
    SourceForm.value_review,
    SourceForm.options,
    SourceForm.field_input,
    SourceForm.summary,
])
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
    labels = [
        button.text
        for row in callback.message.answers[-1][1]["reply_markup"].inline_keyboard
        for button in row
    ]
    assert labels[:4] == [
        "🟠 RSS / Atom", "🔵 Telegram-канал", "⚫ GitHub", "🟠 Hacker News"
    ]


@pytest.mark.asyncio
async def test_back_from_edit_returns_to_source_card():
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
    assert "Изменить" in [
        button.text
        for row in callback.message.answers[-1][1]["reply_markup"].inline_keyboard
        for button in row
    ]


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
async def test_full_report_refuses_catalog_before_starting_wizard(monkeypatch):
    from src.infoservice.bot.handlers import sources

    report_id = uuid4()

    class Repository:
        max_sources_per_report = 30

        def __init__(self, _session):
            pass

        async def list_sources(self, candidate, _user_id):
            assert candidate == report_id
            return [SimpleNamespace(id=index) for index in range(30)]

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    callback = FakeCallback(f"source:catalog:{report_id}")

    await sources.open_catalog(
        callback,
        object(),
        SimpleNamespace(id=uuid4()),
    )

    assert callback.answers[-1] == (
        "В отчёте может быть не более 30 источников",
        {"show_alert": True},
    )


@pytest.mark.asyncio
async def test_existing_beta_source_card_has_no_edit_action(monkeypatch):
    from src.infoservice.bot.handlers import sources

    source_id = uuid4()
    source = SimpleNamespace(
        id=source_id,
        source_type="reddit",
        display_name="r/python",
        enabled=True,
        config={"subreddit": "python"},
    )

    class Repository:
        def __init__(self, _session):
            pass

        async def get_source_owned(self, candidate, _user_id):
            assert candidate == source_id
            return source

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    callback = FakeCallback(f"source:view:{source_id}")

    await sources.view_source(
        callback,
        object(),
        SimpleNamespace(id=uuid4()),
    )

    labels = [
        button.text
        for row in callback.message.answers[-1][1]["reply_markup"].inline_keyboard
        for button in row
    ]
    assert "Изменить" not in labels
    assert "Отключить" in labels
    assert "Удалить" in labels
```

Add a repository-limit test that makes `add_source()` raise
`LimitExceeded("В отчёте может быть не более 30 источников")` and asserts
`save_source()` keeps the draft and presents that exact message as an alert.

- [ ] **Step 2: Run the regression tests**

Run:

```bash
uv run pytest tests/infoservice/bot -v
```

Expected: all tests pass.

- [ ] **Step 3: Update the Russian README with exact commands and four flows**

Add a section to `README_RU.md`:

```markdown
## Управление через Telegram

После запуска откройте системное меню команд Telegram:

- `/menu` — главное меню;
- `/reports` — список отчётов;
- `/newreport` — создать отчёт;
- `/sources` — выбрать отчёт и настроить источники;
- `/settings` — часовой пояс и ключ DeepSeek;
- `/help` — подсказки и примеры;
- `/cancel` — отменить незавершённое действие.

RSS/Atom, публичные Telegram-каналы, GitHub и Hacker News настраиваются
пошаговыми сообщениями. JSON вводить не требуется. Перед сохранением бот
показывает итоговую карточку; отдельные параметры можно изменить кнопкой
«Изменить».
```

- [ ] **Step 4: Run formatting/static checks and the full test suite**

Run:

```bash
uv run pytest -q
```

Expected: the complete suite passes.

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Inspect the final diff for forbidden JSON prompts**

Run:

```bash
rg -n "Отправьте JSON|SOURCE_CONFIG_REQUEST|json.loads\\(message.text\\)" \
  src/infoservice/bot tests/infoservice/bot
```

Expected: no matches.

- [ ] **Step 6: Commit documentation and regression coverage**

```bash
git add README_RU.md tests/infoservice/bot
git commit -m "docs: explain conversational source setup"
```

---

## Final Verification

- [ ] Run the focused bot suite:

```bash
uv run pytest tests/infoservice/bot -v
```

Expected: all bot tests pass.

- [ ] Run source validation and repository regression tests:

```bash
uv run pytest tests/infoservice/sources tests/infoservice/db/test_repositories.py -v
```

Expected: all tests pass.

- [ ] Run the entire repository suite:

```bash
uv run pytest -q
```

Expected: all tests pass with no failures or errors.

- [ ] Confirm a clean implementation diff and intentional commit series:

```bash
git status --short
git log --oneline -7
```

Expected: no uncommitted implementation files; commits include navigation,
stable form parsing, wizard controls, conversational creation, field editing,
and documentation/regression coverage.
