"""Tests for OpenAI-compatible AI client (covers MiniMax, Ali, DeepSeek)."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.client import OpenAIClient, create_ai_client
from src.models import AIConfig, AIProvider


def _make_config(**overrides) -> AIConfig:
    defaults = {
        "provider": AIProvider.MINIMAX,
        "model": "MiniMax-M2.7",
        "api_key_env": "MINIMAX_API_KEY",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    defaults.update(overrides)
    return AIConfig(**defaults)


class TestOpenAIClientInit:
    def test_creates_instance_with_valid_config(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config())
        assert client.model == "MiniMax-M2.7"
        assert client.max_tokens == 4096
        assert client.provider == "minimax"

    def test_raises_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Missing API key"):
            OpenAIClient(_make_config())

    def test_uses_provider_default_base_url(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config())
        assert str(client.client.base_url).rstrip("/").endswith("api.minimax.io/v1")

    def test_uses_custom_base_url(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config(base_url="https://api.minimaxi.com/v1"))
        assert "minimaxi.com" in str(client.client.base_url)

    def test_uses_default_base_url_for_ali(self, monkeypatch):
        monkeypatch.setenv("ALI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.ALI,
            api_key_env="ALI_API_KEY",
        ))
        assert "dashscope.aliyuncs.com" in str(client.client.base_url)


class TestOpenAIClientComplete:
    def test_basic_completion(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config())

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"score": 8}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            result = asyncio.run(client.complete(system="test", user="hello"))

        assert result == '{"score": 8}'
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["model"] == "MiniMax-M2.7"
        # response_format should NOT be present (MiniMax doesn't support it)
        assert "response_format" not in call_kwargs

    def test_temperature_zero_clamped_for_minimax(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config())

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            asyncio.run(client.complete(system="test", user="hello", temperature=0.0))

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["temperature"] > 0

    def test_response_format_present_for_openai(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.OPENAI,
            api_key_env="OPENAI_API_KEY",
        ))

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"score": 8}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            asyncio.run(client.complete(system="test", user="hello"))

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs.get("response_format") == {"type": "json_object"}


class TestTemperatureFallback:
    """Retry-without-temperature path for models that deprecated temperature.

    Triggered by Claude Opus 4.7 on Bedrock Converse and any OpenAI-compatible
    endpoint that rejects `temperature` with a 4xx error message.
    """

    @staticmethod
    def _make_response(text: str = "{}") -> MagicMock:
        resp = MagicMock()
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = text
        resp.usage.prompt_tokens = 1
        resp.usage.completion_tokens = 1
        return resp

    def test_sends_temperature_by_default(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.OPENAI,
            api_key_env="OPENAI_API_KEY",
        ))

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = self._make_response()
            asyncio.run(client.complete(system="s", user="u"))

        assert "temperature" in mock_create.call_args[1]
        assert client._supports_temperature is True

    def test_retries_without_temperature_on_deprecated_error(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.OPENAI,
            api_key_env="OPENAI_API_KEY",
        ))

        first_error = Exception(
            "400 Bad Request: `temperature` is deprecated for this model."
        )
        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = [first_error, self._make_response("ok")]
            result = asyncio.run(client.complete(system="s", user="u"))

        assert result == "ok"
        assert mock_create.call_count == 2
        first_kwargs = mock_create.call_args_list[0][1]
        retry_kwargs = mock_create.call_args_list[1][1]
        assert "temperature" in first_kwargs
        assert "temperature" not in retry_kwargs
        assert client._supports_temperature is False

    def test_does_not_retry_for_unrelated_error(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.OPENAI,
            api_key_env="OPENAI_API_KEY",
        ))

        boom = Exception("500 Internal Server Error")
        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = boom
            with pytest.raises(Exception, match="Internal Server Error"):
                asyncio.run(client.complete(system="s", user="u"))

        assert mock_create.call_count == 1
        assert client._supports_temperature is True

    def test_subsequent_calls_skip_temperature_after_fallback(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.OPENAI,
            api_key_env="OPENAI_API_KEY",
        ))

        client._supports_temperature = False
        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = self._make_response()
            asyncio.run(client.complete(system="s", user="u"))

        assert "temperature" not in mock_create.call_args[1]
        assert mock_create.call_count == 1

    @pytest.mark.parametrize("msg", [
        "`temperature` is deprecated for this model",
        "The model does not support temperature parameter",
        "Unsupported parameter: temperature",
    ])
    def test_detects_various_temperature_error_messages(
        self, monkeypatch, msg
    ):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.OPENAI,
            api_key_env="OPENAI_API_KEY",
        ))

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = [Exception(msg), self._make_response("ok")]
            result = asyncio.run(client.complete(system="s", user="u"))

        assert result == "ok"
        assert mock_create.call_count == 2


class TestFactoryFunction:
    def test_creates_openai_client_for_minimax(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        config = _make_config()
        client = create_ai_client(config)
        assert isinstance(client, OpenAIClient)
        assert client.provider == "minimax"

    def test_creates_openai_client_for_deepseek(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        config = _make_config(
            provider=AIProvider.DEEPSEEK,
            api_key_env="DEEPSEEK_API_KEY",
        )
        client = create_ai_client(config)
        assert isinstance(client, OpenAIClient)
        assert client.provider == "deepseek"

    def test_minimax_provider_enum(self):
        assert AIProvider.MINIMAX.value == "minimax"

    def test_deepseek_provider_enum(self):
        assert AIProvider.DEEPSEEK.value == "deepseek"
