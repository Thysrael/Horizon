from types import SimpleNamespace

from aiogram.types import BotCommand
import pytest

from src.infoservice.bot.commands import BOT_COMMANDS, configure_bot_commands
from src.infoservice.bot.handlers.navigation import (
    cancel_action,
    help_command,
    menu_command,
    settings_command,
)


def test_bot_commands_have_expected_order_and_russian_descriptions():
    assert [item.command for item in BOT_COMMANDS] == [
        "start",
        "menu",
        "reports",
        "newreport",
        "sources",
        "settings",
        "help",
        "cancel",
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
