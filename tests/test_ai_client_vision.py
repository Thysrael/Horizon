"""Tests for AIClient.complete_vision and its provider-specific overrides.

Covers:
- AnthropicClient.complete_vision: multimodal Messages API content block.
- OpenAIClient.complete_vision: OpenAI-compatible `image_url` data-URI content part.
- The base AIClient.complete_vision default (NotImplementedError), verified
  both via a minimal fake subclass and via AzureOpenAIClient/GeminiClient
  (the two concrete clients that intentionally do NOT override it).
- ChainedAIClient.complete_vision delegating to its first/current client only.

All AI SDK clients are mocked; no live network or vision calls are made.
"""

from __future__ import annotations

import asyncio
import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.ai.client import (
    AIClient,
    AnthropicClient,
    AzureOpenAIClient,
    ChainedAIClient,
    GeminiClient,
    OpenAIClient,
)
from src.models import AIConfig, AIProvider

PNG_BYTES = b"\x89PNG\r\n\x1a\n-fake-screenshot-bytes"


def _anthropic_config(**overrides) -> AIConfig:
    defaults = {
        "provider": AIProvider.ANTHROPIC,
        "model": "claude-3-5-sonnet-20241022",
        "api_key_env": "ANTHROPIC_API_KEY",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    defaults.update(overrides)
    return AIConfig(**defaults)


def _openai_config(**overrides) -> AIConfig:
    defaults = {
        "provider": AIProvider.OPENAI,
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    defaults.update(overrides)
    return AIConfig(**defaults)


def _azure_config(**overrides) -> AIConfig:
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


def _gemini_config(**overrides) -> AIConfig:
    defaults = {
        "provider": AIProvider.GEMINI,
        "model": "gemini-1.5-flash",
        "api_key_env": "GOOGLE_API_KEY",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    defaults.update(overrides)
    return AIConfig(**defaults)


class TestAnthropicCompleteVision:
    def test_builds_multimodal_content_block_and_returns_text(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = AnthropicClient(_anthropic_config())

        mock_message = SimpleNamespace(
            content=[SimpleNamespace(text="the real article says X, Y, Z")],
            usage=SimpleNamespace(input_tokens=42, output_tokens=7),
        )

        with patch.object(
            client.client.messages, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_message
            result = asyncio.run(
                client.complete_vision(
                    system="vision system prompt",
                    user="Compare screenshot vs snippet",
                    image_data=PNG_BYTES,
                )
            )

        assert result == "the real article says X, Y, Z"
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["system"] == "vision system prompt"

        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        content_blocks = messages[0]["content"]

        image_blocks = [b for b in content_blocks if b["type"] == "image"]
        text_blocks = [b for b in content_blocks if b["type"] == "text"]
        assert len(image_blocks) == 1
        assert len(text_blocks) == 1
        assert text_blocks[0]["text"] == "Compare screenshot vs snippet"

        image_source = image_blocks[0]["source"]
        assert image_source["type"] == "base64"
        assert image_source["media_type"] == "image/png"
        assert image_source["data"] == base64.b64encode(PNG_BYTES).decode()

    def test_respects_custom_image_media_type(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        client = AnthropicClient(_anthropic_config())

        mock_message = SimpleNamespace(
            content=[SimpleNamespace(text="ok")],
            usage=None,
        )

        with patch.object(
            client.client.messages, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_message
            asyncio.run(
                client.complete_vision(
                    system="sys",
                    user="usr",
                    image_data=PNG_BYTES,
                    image_media_type="image/jpeg",
                )
            )

        content_blocks = mock_create.call_args[1]["messages"][0]["content"]
        image_block = next(b for b in content_blocks if b["type"] == "image")
        assert image_block["source"]["media_type"] == "image/jpeg"


class TestOpenAICompleteVision:
    def test_builds_image_url_data_uri_and_returns_text(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_openai_config())

        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="extracted real content"))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20),
        )

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            result = asyncio.run(
                client.complete_vision(
                    system="vision system prompt",
                    user="Compare screenshot vs snippet",
                    image_data=PNG_BYTES,
                )
            )

        assert result == "extracted real content"
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"

        messages = call_kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "vision system prompt"}
        user_content = messages[1]["content"]
        text_parts = [p for p in user_content if p["type"] == "text"]
        image_parts = [p for p in user_content if p["type"] == "image_url"]
        assert text_parts[0]["text"] == "Compare screenshot vs snippet"

        expected_data_url = f"data:image/png;base64,{base64.b64encode(PNG_BYTES).decode()}"
        assert image_parts[0]["image_url"]["url"] == expected_data_url

    def test_minimax_provider_skips_response_format_for_vision(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        client = OpenAIClient(
            _openai_config(provider=AIProvider.MINIMAX, model="MiniMax-M3", api_key_env="MINIMAX_API_KEY")
        )

        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=None,
        )

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response
            asyncio.run(
                client.complete_vision(system="s", user="u", image_data=PNG_BYTES)
            )

        assert "response_format" not in mock_create.call_args[1]

    def test_retries_without_temperature_on_deprecated_error(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        client = OpenAIClient(_openai_config())

        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=None,
        )

        with patch.object(
            client.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = [
                Exception("`temperature` is deprecated for this model."),
                mock_response,
            ]
            result = asyncio.run(
                client.complete_vision(system="s", user="u", image_data=PNG_BYTES)
            )

        assert result == "ok"
        assert mock_create.call_count == 2
        assert "temperature" in mock_create.call_args_list[0][1]
        assert "temperature" not in mock_create.call_args_list[1][1]


class TestBaseCompleteVisionDefault:
    """Providers that don't override complete_vision inherit NotImplementedError."""

    def test_minimal_subclass_without_override_raises_not_implemented(self):
        class _MinimalClient(AIClient):
            async def complete(self, system, user, temperature=None, max_tokens=None):
                return "unused"

        client = _MinimalClient()

        with pytest.raises(NotImplementedError, match="_MinimalClient"):
            asyncio.run(
                client.complete_vision(system="s", user="u", image_data=PNG_BYTES)
            )

    def test_azure_client_does_not_override_complete_vision(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
        client = AzureOpenAIClient(_azure_config())

        with pytest.raises(NotImplementedError, match="AzureOpenAIClient"):
            asyncio.run(
                client.complete_vision(system="s", user="u", image_data=PNG_BYTES)
            )

    def test_gemini_client_does_not_override_complete_vision(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        client = GeminiClient(_gemini_config())

        with pytest.raises(NotImplementedError, match="GeminiClient"):
            asyncio.run(
                client.complete_vision(system="s", user="u", image_data=PNG_BYTES)
            )


class TestChainedCompleteVision:
    """ChainedAIClient.complete_vision delegates to its first/current client only."""

    def test_delegates_to_first_client_on_success(self):
        cfg1 = AIConfig(provider=AIProvider.OPENAI, model="m1", api_key_env="K1")
        cfg2 = AIConfig(provider=AIProvider.OLLAMA, model="m2", api_key_env="")

        class _VisionCapableDummy:
            def __init__(self, result):
                self.result = result
                self.calls = []

            async def complete_vision(self, system, user, image_data, image_media_type="image/png", temperature=None, max_tokens=None):
                self.calls.append((system, user, image_data, image_media_type, temperature, max_tokens))
                return self.result

        client1 = _VisionCapableDummy(result="vision text from provider 1")
        client2 = _VisionCapableDummy(result="should never be called")

        chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])
        result = asyncio.run(
            chained.complete_vision(system="sys", user="usr", image_data=PNG_BYTES)
        )

        assert result == "vision text from provider 1"
        assert len(client1.calls) == 1
        assert len(client2.calls) == 0

    def test_propagates_not_implemented_error_from_first_client_without_fallback(self):
        cfg1 = AIConfig(provider=AIProvider.AZURE, model="m1", api_key_env="K1")
        cfg2 = AIConfig(provider=AIProvider.OPENAI, model="m2", api_key_env="K2")

        class _NonVisionDummy:
            async def complete_vision(self, *args, **kwargs):
                raise NotImplementedError("_NonVisionDummy does not support vision/image input")

        class _NeverCalledDummy:
            def __init__(self):
                self.called = False

            async def complete_vision(self, *args, **kwargs):
                self.called = True
                return "should not happen"

        client1 = _NonVisionDummy()
        client2 = _NeverCalledDummy()

        chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])

        with pytest.raises(NotImplementedError):
            asyncio.run(
                chained.complete_vision(system="sys", user="usr", image_data=PNG_BYTES)
            )

        # Unlike complete(), complete_vision does NOT fall back to the next provider.
        assert client2.called is False

    def test_does_not_construct_downstream_clients_when_first_succeeds(self):
        cfg1 = AIConfig(provider=AIProvider.OPENAI, model="m1", api_key_env="K1")
        cfg2 = AIConfig(provider=AIProvider.OLLAMA, model="m2", api_key_env="")

        class _VisionCapableDummy:
            async def complete_vision(self, *args, **kwargs):
                return "ok"

        factory_calls = []

        def factory(cfg):
            factory_calls.append(cfg)
            return _VisionCapableDummy()

        chained = ChainedAIClient([cfg1, cfg2], client_factory=factory)
        result = asyncio.run(
            chained.complete_vision(system="sys", user="usr", image_data=PNG_BYTES)
        )

        assert result == "ok"
        assert len(factory_calls) == 1
        assert factory_calls[0].provider == AIProvider.OPENAI
