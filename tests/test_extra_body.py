"""Tests for ai.extra_body passthrough to provider request bodies."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from src.ai.client import (
    AnthropicClient,
    AzureOpenAIClient,
    GeminiClient,
    OpenAIClient,
    _create_chained_client,
)
from src.models import AIConfig, AIProvider

EXTRA_BODY = {"chat_template_kwargs": {"enable_thinking": False}}


def _openai_response():
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))],
        usage=None,
    )


def _ollama_config(**overrides) -> AIConfig:
    defaults = {"provider": AIProvider.OLLAMA, "model": "qwen3", "api_key_env": ""}
    defaults.update(overrides)
    return AIConfig(**defaults)


def _complete_openai(client) -> dict:
    create = AsyncMock(return_value=_openai_response())
    client.client.chat.completions.create = create
    asyncio.run(client.complete(system="s", user="u"))
    return create.call_args.kwargs


def test_openai_compatible_client_sends_extra_body() -> None:
    kwargs = _complete_openai(OpenAIClient(_ollama_config(extra_body=EXTRA_BODY)))

    assert kwargs["extra_body"] == EXTRA_BODY
    assert kwargs["response_format"] == {"type": "json_object"}


def test_openai_compatible_client_omits_extra_body_by_default() -> None:
    kwargs = _complete_openai(OpenAIClient(_ollama_config()))

    assert "extra_body" not in kwargs


def test_azure_client_sends_extra_body(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    config = AIConfig(
        provider=AIProvider.AZURE,
        model="gpt-4o-deployment",
        api_key_env="AZURE_OPENAI_API_KEY",
        azure_endpoint_env="AZURE_OPENAI_ENDPOINT",
        api_version="2024-10-21",
        extra_body=EXTRA_BODY,
    )

    kwargs = _complete_openai(AzureOpenAIClient(config))

    assert kwargs["extra_body"] == EXTRA_BODY


def test_anthropic_client_sends_extra_body(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = AnthropicClient(
        AIConfig(
            provider=AIProvider.ANTHROPIC,
            model="claude-test",
            api_key_env="ANTHROPIC_API_KEY",
            extra_body={"metadata": {"user_id": "horizon"}},
        )
    )
    create = AsyncMock(
        return_value=SimpleNamespace(
            content=[SimpleNamespace(type="text", text="{}")], usage=None
        )
    )
    client.client.messages.create = create

    asyncio.run(client.complete(system="s", user="u"))

    assert create.call_args.kwargs["extra_body"] == {"metadata": {"user_id": "horizon"}}


def test_anthropic_client_skips_thinking_blocks(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = AnthropicClient(
        AIConfig(
            provider=AIProvider.ANTHROPIC,
            model="claude-test",
            api_key_env="ANTHROPIC_API_KEY",
            extra_body={"thinking": {"type": "enabled", "budget_tokens": 1024}},
        )
    )
    client.client.messages.create = AsyncMock(
        return_value=SimpleNamespace(
            content=[
                SimpleNamespace(type="thinking", thinking="reasoning", signature="sig"),
                SimpleNamespace(type="text", text='{"ok": true}'),
            ],
            usage=None,
        )
    )

    assert asyncio.run(client.complete(system="s", user="u")) == '{"ok": true}'


def test_gemini_client_rejects_extra_body(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    config = AIConfig(
        provider=AIProvider.GEMINI,
        model="gemini-test",
        api_key_env="GOOGLE_API_KEY",
        extra_body=EXTRA_BODY,
    )

    with pytest.raises(ValueError, match="extra_body is not supported"):
        GeminiClient(config)


def test_provider_chain_applies_extra_body_only_to_primary_provider() -> None:
    config = _ollama_config(provider_chain="ollama,openai", extra_body=EXTRA_BODY)

    ollama, openai = _create_chained_client(config).configs

    assert ollama.extra_body == EXTRA_BODY
    assert openai.extra_body is None


def test_extra_body_must_be_an_object() -> None:
    with pytest.raises(ValidationError):
        _ollama_config(extra_body=["enable_thinking"])
