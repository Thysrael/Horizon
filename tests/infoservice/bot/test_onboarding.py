import pytest
from aiogram.types import Message

from src.infoservice.bot.handlers.start import start
from src.infoservice.bot.keyboards import MAIN_MENU_CALLBACKS
from src.infoservice.bot.messages_ru import GROUP_PRIVATE_REDIRECT, TIMEZONE_REQUEST
from src.infoservice.bot.middleware import PrivateUserMiddleware
from src.infoservice.bot.states import Onboarding


def test_main_menu_exposes_the_required_callback_ids():
    assert MAIN_MENU_CALLBACKS == ("reports", "llm", "settings", "help")


def test_onboarding_has_a_timezone_state():
    assert Onboarding.timezone.state.endswith(":timezone")


def test_onboarding_messages_are_in_russian():
    assert "часовой пояс" in TIMEZONE_REQUEST.lower()
    assert "личный чат" in GROUP_PRIVATE_REDIRECT.lower()


@pytest.mark.asyncio
async def test_start_enters_timezone_onboarding_and_offers_timezone_keyboard():
    replies = []

    class State:
        value = None

        async def set_state(self, value):
            self.value = value

    class Message:
        async def answer(self, text, **kwargs):
            replies.append((text, kwargs))

    state = State()
    await start(Message(), state)

    assert state.value == Onboarding.timezone
    assert "часовой пояс" in replies[0][0].lower()
    assert replies[0][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_group_message_is_redirected_before_a_user_or_session_is_created(monkeypatch):
    replies = []

    async def answer(self, text, **kwargs):
        replies.append(text)

    monkeypatch.setattr(Message, "answer", answer)
    message = Message.model_validate({
        "message_id": 1,
        "date": 0,
        "chat": {"id": -100, "type": "group"},
        "from": {"id": 1001, "is_bot": False, "first_name": "Ada"},
        "text": "/start",
    })

    def session_factory():
        raise AssertionError("group messages must not open a database session")

    async def handler(event, data):
        raise AssertionError("group messages must not reach a handler")

    await PrivateUserMiddleware(session_factory)(handler, message, {})

    assert replies == [GROUP_PRIVATE_REDIRECT]
