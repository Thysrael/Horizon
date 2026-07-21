from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from src.infoservice.bot.handlers import credentials
from src.infoservice.bot.handlers.credentials import add_key, delete_deepseek_key, encrypt_deepseek_key, receive_key, replace_key
from src.infoservice.llm.deepseek import CredentialVerificationUnavailable
from src.infoservice.security.credentials import CredentialCipher


def test_key_flow_only_returns_ciphertext():
    secret = "sk-user-secret"
    ciphertext, mask = encrypt_deepseek_key(CredentialCipher(Fernet.generate_key().decode()), secret)

    assert secret not in ciphertext
    assert mask == "sk-…cret"


@pytest.mark.asyncio
async def test_received_key_is_deleted_and_persisted_only_as_ciphertext(monkeypatch):
    key = "sk-user-secret"
    saved = []

    class Repository:
        def __init__(self, session):
            pass

        async def upsert(self, user_id, data):
            saved.append(data)

    class Verifier:
        def verify(self, candidate):
            assert candidate == key

    async def run_in_test_executor(function, *args):
        return function(*args)

    class Message:
        text = key
        deleted = False

        async def answer(self, *args, **kwargs):
            pass

        async def delete(self):
            self.deleted = True

    class State:
        cleared = False

        async def clear(self):
            self.cleared = True

    monkeypatch.setattr(credentials, "CredentialRepository", Repository)
    monkeypatch.setattr(credentials.asyncio, "to_thread", run_in_test_executor)
    message = Message()
    state = State()
    cipher = CredentialCipher(Fernet.generate_key().decode())

    class Session:
        async def execute(self, statement):
            pass

    await receive_key(message, state, Session(), SimpleNamespace(id="user-id"), cipher, Verifier())

    assert message.deleted is True
    assert state.cleared is True
    assert key.encode() not in saved[0].ciphertext
    assert cipher.decrypt(saved[0].ciphertext.decode()) == key


@pytest.mark.asyncio
async def test_deleting_key_disables_the_users_reports():
    credential = object()

    class Session:
        def __init__(self):
            self.deleted = []
            self.executed = []
            self.flushed = False

        async def scalar(self, statement):
            return credential

        async def delete(self, value):
            self.deleted.append(value)

        async def execute(self, statement):
            self.executed.append(statement)

        async def flush(self):
            self.flushed = True

    session = Session()
    assert await delete_deepseek_key(session, SimpleNamespace(id="user-id")) is True
    assert session.deleted == [credential]
    assert len(session.executed) == 1
    assert session.flushed is True


@pytest.mark.asyncio
async def test_adding_when_a_key_exists_requires_replacement_confirmation():
    replies = []

    class Callback:
        class Message:
            async def answer(self, text, **kwargs):
                replies.append((text, kwargs))

        message = Message()

        async def answer(self):
            pass

    class State:
        value = None

        async def set_state(self, value):
            self.value = value

    class Session:
        async def scalar(self, statement):
            return object()

    state = State()
    await add_key(Callback(), state, Session(), SimpleNamespace(id="user-id"))

    assert state.value == credentials.Credentials.replace_confirmation
    assert "заменить" in replies[0][0].lower()


@pytest.mark.asyncio
async def test_verifier_failure_still_deletes_submitted_key(monkeypatch):
    class Verifier:
        def verify(self, candidate):
            raise CredentialVerificationUnavailable()

    async def run_in_test_executor(function, *args):
        return function(*args)

    class Message:
        text = "sk-user-secret"
        deleted = False

        async def answer(self, *args, **kwargs):
            pass

        async def delete(self):
            self.deleted = True

    monkeypatch.setattr(credentials.asyncio, "to_thread", run_in_test_executor)
    message = Message()

    await receive_key(message, object(), object(), SimpleNamespace(id="user-id"), object(), Verifier())

    assert message.deleted is True


@pytest.mark.asyncio
async def test_successful_key_add_reenables_reports_after_a_delete(monkeypatch):
    key = "sk-user-secret"

    class Repository:
        def __init__(self, session):
            pass

        async def upsert(self, user_id, data):
            pass

    class Verifier:
        def verify(self, candidate):
            assert candidate == key

    async def run_in_test_executor(function, *args):
        return function(*args)

    class Message:
        text = key

        async def answer(self, *args, **kwargs):
            pass

        async def delete(self):
            pass

    class State:
        async def clear(self):
            pass

    class Session:
        def __init__(self):
            self.executed = []

        async def execute(self, statement):
            self.executed.append(statement)

    monkeypatch.setattr(credentials, "CredentialRepository", Repository)
    monkeypatch.setattr(credentials.asyncio, "to_thread", run_in_test_executor)
    session = Session()

    await receive_key(Message(), State(), session, SimpleNamespace(id="user-id"), CredentialCipher(Fernet.generate_key().decode()), Verifier())

    assert len(session.executed) == 1
    assert session.executed[0].compile().params["enabled"] is True


@pytest.mark.asyncio
async def test_replace_key_answers_callback_once(monkeypatch):
    answer_calls = 0

    class Callback:
        async def answer(self):
            nonlocal answer_calls
            answer_calls += 1

    async def delegated_add_key(callback, state, session, user):
        await callback.answer()

    monkeypatch.setattr(credentials, "add_key", delegated_add_key)

    await replace_key(Callback(), object(), object(), object())

    assert answer_calls == 1
