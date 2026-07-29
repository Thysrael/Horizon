"""Tests for the local Codex CLI AI client."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from src.ai.client import CodexCLIClient, create_ai_client
from src.models import AIConfig, AIProvider


def _config(model: str = "default") -> AIConfig:
    return AIConfig(
        provider=AIProvider.CODEX,
        model=model,
        api_key_env="",
    )


class _Process:
    def __init__(
        self,
        stdout: bytes = b'{"score": 8}',
        stderr: bytes = b"",
        returncode: int = 0,
    ):
        self.returncode = returncode
        self.communicate = AsyncMock(return_value=(stdout, stderr))
        self.kill = Mock()
        self.wait = AsyncMock()


def test_factory_creates_codex_client(monkeypatch):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")

    client = create_ai_client(_config())

    assert isinstance(client, CodexCLIClient)
    assert client.binary == "/usr/bin/codex"


def test_missing_binary_has_actionable_error(monkeypatch):
    monkeypatch.delenv("HORIZON_CODEX_BIN", raising=False)
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: None)

    with pytest.raises(ValueError, match="Codex CLI was not found"):
        CodexCLIClient(_config())


@pytest.mark.parametrize("value", ["0", "-1", "not-a-number", "nan", "inf"])
def test_timeout_must_be_positive_and_finite(monkeypatch, value):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    monkeypatch.setenv("HORIZON_CODEX_TIMEOUT_SEC", value)

    with pytest.raises(ValueError, match="must be a positive number"):
        CodexCLIClient(_config())


def test_default_model_is_omitted_and_sandbox_is_read_only(monkeypatch):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    client = CodexCLIClient(_config())

    command = client._build_command()

    assert "--model" not in command
    assert command[-1] == "-"
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert "--ephemeral" in command
    assert "--ignore-user-config" in command


def test_explicit_model_is_forwarded(monkeypatch):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    client = CodexCLIClient(_config("gpt-5.6-terra"))

    command = client._build_command()

    model_index = command.index("--model")
    assert command[model_index + 1] == "gpt-5.6-terra"


def test_complete_uses_stdin_and_an_empty_temporary_workdir(monkeypatch):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    process = _Process()
    create = AsyncMock(return_value=process)
    monkeypatch.setattr("src.ai.client.asyncio.create_subprocess_exec", create)
    client = CodexCLIClient(_config())

    result = asyncio.run(client.complete(system="system text", user="user text"))

    assert result == '{"score": 8}'
    stdin = process.communicate.await_args.args[0].decode()
    assert "<system>\nsystem text\n</system>" in stdin
    assert "<user>\nuser text\n</user>" in stdin
    workdir = Path(create.await_args.kwargs["cwd"])
    assert workdir.name.startswith("horizon-codex-")
    assert not workdir.exists()


def test_complete_raises_on_nonzero_exit_and_truncates_stderr(monkeypatch):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    stderr = b"x" * 3000 + b"login required"
    process = _Process(stderr=stderr, returncode=1)
    monkeypatch.setattr(
        "src.ai.client.asyncio.create_subprocess_exec",
        AsyncMock(return_value=process),
    )
    client = CodexCLIClient(_config())

    with pytest.raises(RuntimeError) as exc_info:
        asyncio.run(client.complete(system="s", user="u"))

    assert "login required" in str(exc_info.value)
    assert len(str(exc_info.value)) < 2100


def test_complete_rejects_empty_response(monkeypatch):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    process = _Process(stdout=b" \n")
    monkeypatch.setattr(
        "src.ai.client.asyncio.create_subprocess_exec",
        AsyncMock(return_value=process),
    )
    client = CodexCLIClient(_config())

    with pytest.raises(RuntimeError, match="empty response"):
        asyncio.run(client.complete(system="s", user="u"))


def test_timeout_kills_and_waits_for_process(monkeypatch):
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    monkeypatch.setenv("HORIZON_CODEX_TIMEOUT_SEC", "1")
    process = _Process()
    process.communicate = AsyncMock(side_effect=TimeoutError)
    monkeypatch.setattr(
        "src.ai.client.asyncio.create_subprocess_exec",
        AsyncMock(return_value=process),
    )
    client = CodexCLIClient(_config())

    with pytest.raises(TimeoutError, match="timed out after 1s"):
        asyncio.run(client.complete(system="s", user="u"))

    process.kill.assert_called_once_with()
    process.wait.assert_awaited_once_with()
