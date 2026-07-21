from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from aiogram.types import Message

from src.infoservice.bot.app import create_dispatcher
from src.infoservice.bot.handlers.start import start, timezone_text
from src.infoservice.bot.keyboards import MAIN_MENU_CALLBACKS
from src.infoservice.bot.messages_ru import GROUP_PRIVATE_REDIRECT, TIMEZONE_INVALID, TIMEZONE_REQUEST
from src.infoservice.bot.middleware import PrivateUserMiddleware
from src.infoservice.bot.states import Onboarding
from src.infoservice.settings import Settings


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


def test_dispatcher_registers_user_middleware_on_message_and_callback_observers():
    settings = Settings(
        database_url="postgresql+asyncpg://unused",
        telegram_bot_token="token",
        app_encryption_key=Fernet.generate_key().decode(),
    )
    session_factory = object()

    dispatcher = create_dispatcher(settings, session_factory)

    for observer in (dispatcher.message, dispatcher.callback_query):
        middlewares = observer.outer_middleware._middlewares
        assert len(middlewares) == 1
        assert isinstance(middlewares[0], PrivateUserMiddleware)
        assert middlewares[0]._session_factory is session_factory


@pytest.mark.asyncio
async def test_dispatcher_message_middleware_injects_session_and_user_into_handler(monkeypatch):
    message = Message.model_validate({
        "message_id": 1,
        "date": 0,
        "chat": {"id": 1001, "type": "private"},
        "from": {"id": 1001, "is_bot": False, "first_name": "Ada"},
        "text": "/start",
    })
    session = SimpleNamespace(committed=False, rolled_back=False)

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *args):
            return None

    async def commit():
        session.committed = True

    async def rollback():
        session.rolled_back = True

    session.commit = commit
    session.rollback = rollback
    async def get_or_create(*_):
        return SimpleNamespace(id="user-id")

    monkeypatch.setattr("src.infoservice.bot.middleware.UserRepository.get_or_create", get_or_create)

    middleware = PrivateUserMiddleware(lambda: SessionContext())
    received = {}

    async def handler(event, data):
        received.update(data)

    await middleware(handler, message, {})

    assert received["session"] is session
    assert received["user"].id == "user-id"
    assert session.committed is True


@pytest.mark.asyncio
async def test_valid_timezone_is_flushed_and_invalid_timezone_is_not_persisted():
    replies = []

    class Message:
        text = "Europe/Moscow"

        async def answer(self, text, **kwargs):
            replies.append((text, kwargs))

    class State:
        cleared = False

        async def clear(self):
            self.cleared = True

    class Session:
        flushed = 0

        async def flush(self):
            self.flushed += 1

    user = SimpleNamespace(timezone="UTC")
    message, state, session = Message(), State(), Session()

    await timezone_text(message, state, session, user)

    assert user.timezone == "Europe/Moscow"
    assert session.flushed == 1
    assert state.cleared is True

    message.text = "Not/A_Timezone"
    state.cleared = False
    await timezone_text(message, state, session, user)

    assert user.timezone == "Europe/Moscow"
    assert session.flushed == 1
    assert state.cleared is False
    assert replies[-1][0] == TIMEZONE_INVALID
