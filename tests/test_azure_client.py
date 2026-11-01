"""Tests for Azure OpenAI client."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import httpx
from openai import BadRequestError

from src.ai.client import AzureOpenAIClient, create_ai_client
from src.models import AIConfig, AIProvider


def _make_config(**overrides) -> AIConfig:
    defaults = {
        "provider": AIProvider.AZURE,
        "model": "gpt-4o-deployment",
        "api_key_env": "AZURE_OPENAI_API_KEY",
        "azure_endpoint_env": "AZURE_OPENAI_ENDPOINT",
        "api_version": "2024-10-21",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    defaults.update(overrides)
    return AIConfig(**defaults)


def _mock_response(content: str = '{"ok": true}'):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )


class TestAzureOpenAIClientInit:
    def test_creates_instance_with_valid_config(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")

        client = AzureOpenAIClient(_make_config())

        assert client.model == "gpt-4o-deployment"
        assert client.max_tokens == 4096

    def test_raises_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")

        with pytest.raises(ValueError, match="Missing API key"):
            AzureOpenAIClient(_make_config())

    def test_raises_when_endpoint_missing(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)

        with pytest.raises(ValueError, match="Missing Azure endpoint"):
            AzureOpenAIClient(_make_config())


class TestAzureOpenAIClientComplete:
    def test_uses_max_completion_tokens_for_gpt5_prefix(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
        client = AzureOpenAIClient(_make_config(model="gpt-5-mini"))

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = _mock_response()
            asyncio.run(client.complete(system="test", user="hello"))

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 4096
        assert "max_tokens" not in call_kwargs

    def test_retries_with_max_completion_tokens_for_custom_deployment(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
        client = AzureOpenAIClient(_make_config(model="prod-gpt5-nano"))

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = [
                BadRequestError(
                    "Unsupported parameter: 'max_tokens'. Use 'max_completion_tokens' instead.",
                    response=httpx.Response(400, request=httpx.Request("POST", "https://example.com")),
                    body=None,
                ),
                _mock_response(),
            ]
            result = asyncio.run(client.complete(system="test", user="hello"))

        assert result == '{"ok": true}'
        first_call = mock_create.call_args_list[0].kwargs
        second_call = mock_create.call_args_list[1].kwargs
        assert first_call["max_tokens"] == 4096
        assert "max_completion_tokens" not in first_call
        assert second_call["max_completion_tokens"] == 4096
        assert "max_tokens" not in second_call
        assert client._use_max_completion_tokens is True


class TestFactoryFunction:
    def test_creates_azure_client(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")

        client = create_ai_client(_make_config())

        assert isinstance(client, AzureOpenAIClient)
