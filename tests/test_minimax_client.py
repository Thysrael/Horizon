"""Tests for OpenAI-compatible AI client (covers MiniMax, Ali, DeepSeek)."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from anthropic import AsyncAnthropic

from src.ai.client import AnthropicClient, OpenAIClient, create_ai_client
from src.models import AIConfig, AIProvider, AI_PROVIDER_DEFAULTS


def _make_config(**overrides) -> AIConfig:
    defaults = {
        "provider": AIProvider.MINIMAX,
        "model": "MiniMax-M3",
        "api_key_env": "MINIMAX_API_KEY",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    defaults.update(overrides)
    return AIConfig(**defaults)


def _make_ollama_config(**overrides) -> AIConfig:
    defaults = {
        "provider": AIProvider.OLLAMA,
        "model": "llama3.1",
        "api_key_env": "",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    defaults.update(overrides)
    return AIConfig(**defaults)


class TestOpenAIClientInit:
    def test_creates_instance_with_valid_config(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config())
        assert client.model == "MiniMax-M3"
        assert client.max_tokens == 4096
        assert client.provider == "minimax"

    def test_raises_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Missing API key"):
            OpenAIClient(_make_config())

    def test_rejects_literal_api_key_in_api_key_env_without_leaking_it(self, monkeypatch):
        literal_key = "sk-test1234567890"
        monkeypatch.delenv(literal_key, raising=False)

        with pytest.raises(ValueError) as exc:
            OpenAIClient(_make_config(api_key_env=literal_key))

        message = str(exc.value)
        assert literal_key not in message
        assert "api_key_env" in message
        assert "environment variable name" in message
        assert "MINIMAX_API_KEY" in message

    def test_does_not_echo_identifier_shaped_api_key(self, monkeypatch):
        literal_key = "a2c9f1b4e6d7a3c0b5e8d1f9a4c2e6b8"
        monkeypatch.delenv(literal_key, raising=False)

        with pytest.raises(ValueError) as exc:
            OpenAIClient(_make_config(api_key_env=literal_key))

        message = str(exc.value)
        assert literal_key not in message
        assert "api_key_env" in message
        assert "MINIMAX_API_KEY" in message

    def test_uses_provider_default_base_url(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config())
        assert str(client.client.base_url).rstrip("/").endswith("api.minimax.io/v1")

    def test_uses_china_openai_compatible_base_url(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(_make_config(base_url="https://api.minimaxi.com/v1"))
        assert str(client.client.base_url).rstrip("/") == "https://api.minimaxi.com/v1"

    def test_uses_default_base_url_for_ali(self, monkeypatch):
        monkeypatch.setenv("ALI_API_KEY", "test-key")
        client = OpenAIClient(_make_config(
            provider=AIProvider.ALI,
            api_key_env="ALI_API_KEY",
        ))
        assert "dashscope.aliyuncs.com" in str(client.client.base_url)

    def test_ollama_uses_localhost_default_base_url(self, monkeypatch):
        monkeypatch.delenv("HORIZON_OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_HOST", raising=False)

        client = OpenAIClient(_make_ollama_config())

        assert str(client.client.base_url).rstrip("/") == "http://localhost:11434/v1"

    def test_ollama_accepts_custom_base_url_without_v1(self, monkeypatch):
        monkeypatch.delenv("HORIZON_OLLAMA_BASE_URL", raising=False)

        client = OpenAIClient(_make_ollama_config(base_url="http://192.168.1.10:11434"))

        assert str(client.client.base_url).rstrip("/") == "http://192.168.1.10:11434/v1"

    def test_ollama_does_not_duplicate_v1_in_custom_base_url(self, monkeypatch):
        monkeypatch.delenv("HORIZON_OLLAMA_BASE_URL", raising=False)

        client = OpenAIClient(_make_ollama_config(base_url="https://ollama.example/v1/"))

        assert str(client.client.base_url).rstrip("/") == "https://ollama.example/v1"

    def test_ollama_uses_base_url_from_env(self, monkeypatch):
        monkeypatch.setenv("HORIZON_OLLAMA_BASE_URL", "http://ollama.internal:11434")

        client = OpenAIClient(_make_ollama_config())

        assert str(client.client.base_url).rstrip("/") == "http://ollama.internal:11434/v1"

    def test_ollama_config_base_url_overrides_env(self, monkeypatch):
        monkeypatch.setenv("HORIZON_OLLAMA_BASE_URL", "http://env-host:11434")

        client = OpenAIClient(_make_ollama_config(base_url="http://config-host:11434"))

        assert str(client.client.base_url).rstrip("/") == "http://config-host:11434/v1"

    def test_ollama_host_env_without_scheme_is_supported(self, monkeypatch):
        monkeypatch.delenv("HORIZON_OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.setenv("OLLAMA_HOST", "nas.local:11434")

        client = OpenAIClient(_make_ollama_config())

        assert str(client.client.base_url).rstrip("/") == "http://nas.local:11434/v1"


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
        assert call_kwargs["model"] == "MiniMax-M3"
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
    def test_minimax_provider_defaults(self):
        defaults = AI_PROVIDER_DEFAULTS[AIProvider.MINIMAX]
        assert defaults["model"] == "MiniMax-M3"
        assert defaults["base_url"] == "https://api.minimax.io/v1"

    def test_creates_openai_client_for_minimax(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        config = _make_config()
        client = create_ai_client(config)
        assert isinstance(client, OpenAIClient)
        assert client.provider == "minimax"

    @pytest.mark.parametrize(
        "base_url",
        [
            "https://api.minimax.io/anthropic",
            "https://api.minimaxi.com/anthropic",
        ],
    )
    def test_anthropic_compatible_base_url_builds_messages_path(
        self, monkeypatch, base_url
    ):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        requests = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "id": "msg_test",
                    "type": "message",
                    "role": "assistant",
                    "model": "MiniMax-M3",
                    "content": [{"type": "text", "text": "ok"}],
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                },
            )

        async def run_request() -> str:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as http_client:
                sdk_client = AsyncAnthropic(
                    api_key="test-key",
                    base_url=base_url,
                    http_client=http_client,
                )
                with patch("src.ai.client.AsyncAnthropic", return_value=sdk_client):
                    client = create_ai_client(_make_config(base_url=base_url))
                    assert isinstance(client, AnthropicClient)
                    return await client.complete(system="test", user="hello")

        assert asyncio.run(run_request()) == "ok"
        assert [str(request.url) for request in requests] == [
            f"{base_url}/v1/messages"
        ]

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
