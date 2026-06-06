"""Tests for ChainedAIClient fallback logic."""

import asyncio
from datetime import datetime, timezone

import pytest

from src.ai.client import ChainedAIClient, _create_chained_client
from src.models import AIConfig, AIProvider, ContentItem, SourceType


class _DummyClient:
    """Mock AI client for testing."""

    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc
        self.calls = []

    async def complete(self, system, user, temperature=None, max_tokens=None):
        self.calls.append((system, user, temperature, max_tokens))
        if self.exc:
            raise self.exc
        return self.result


class _MockFactory:
    """Factory that returns pre-built dummy clients in order."""

    def __init__(self, *clients):
        self.clients = list(clients)
        self.calls = []
        self.idx = 0

    def __call__(self, cfg):
        self.calls.append(cfg)
        client = self.clients[self.idx]
        self.idx += 1
        return client


def _make_config(provider: AIProvider, model: str = "m", api_key_env: str = "K") -> AIConfig:
    return AIConfig(
        provider=provider,
        model=model,
        api_key_env=api_key_env,
    )


def test_success_on_first_provider():
    """When first provider succeeds, no fallback occurs."""
    cfg1 = _make_config(AIProvider.OPENAI)
    cfg2 = _make_config(AIProvider.OLLAMA)
    client1 = _DummyClient(result="ok")
    client2 = _DummyClient(result="also ok")

    chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])
    result = asyncio.run(chained.complete("sys", "usr"))

    assert result == "ok"
    assert len(client1.calls) == 1
    assert len(client2.calls) == 0


def test_fallback_on_empty_response():
    """When first provider returns empty/whitespace, fallback to second."""
    cfg1 = _make_config(AIProvider.OPENAI)
    cfg2 = _make_config(AIProvider.OLLAMA)
    client1 = _DummyClient(result="   ")
    client2 = _DummyClient(result="fallback ok")

    chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])
    result = asyncio.run(chained.complete("sys", "usr"))

    assert result == "fallback ok"
    assert len(client1.calls) == 1
    assert len(client2.calls) == 1


def test_fallback_on_rate_limit():
    """When first provider hits 429, fallback to second."""
    cfg1 = _make_config(AIProvider.OPENAI)
    cfg2 = _make_config(AIProvider.OLLAMA)
    client1 = _DummyClient(exc=Exception("429 rate limit exceeded"))
    client2 = _DummyClient(result="fallback ok")

    chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])
    result = asyncio.run(chained.complete("sys", "usr"))

    assert result == "fallback ok"
    assert len(client1.calls) == 1
    assert len(client2.calls) == 1


def test_fallback_on_quota_exceeded():
    """When first provider quota exhausted, fallback to second."""
    cfg1 = _make_config(AIProvider.OPENAI)
    cfg2 = _make_config(AIProvider.GEMINI)
    client1 = _DummyClient(exc=Exception("403 quota exceeded"))
    client2 = _DummyClient(result="fallback ok")

    chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])
    result = asyncio.run(chained.complete("sys", "usr"))

    assert result == "fallback ok"


def test_all_providers_fail():
    """When all providers fail, raise RuntimeError."""
    cfg1 = _make_config(AIProvider.OPENAI)
    cfg2 = _make_config(AIProvider.OLLAMA)
    client1 = _DummyClient(exc=Exception("429 rate limit"))
    client2 = _DummyClient(exc=Exception("503 service unavailable"))

    chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])
    with pytest.raises(RuntimeError, match="All providers failed"):
        asyncio.run(chained.complete("sys", "usr"))


def test_no_fallback_on_unexpected_error():
    """Non-retryable errors should not trigger fallback."""
    cfg1 = _make_config(AIProvider.OPENAI)
    cfg2 = _make_config(AIProvider.OLLAMA)
    client1 = _DummyClient(exc=ValueError("Invalid JSON schema"))
    client2 = _DummyClient(result="fallback ok")

    chained = ChainedAIClient([cfg1, cfg2], clients=[client1, client2])
    with pytest.raises(ValueError, match="Invalid JSON schema"):
        asyncio.run(chained.complete("sys", "usr"))

    assert len(client2.calls) == 0


def test_should_fallback_detects_retryable_errors():
    """_should_fallback correctly identifies retryable errors."""
    assert ChainedAIClient._should_fallback(Exception("429 rate limit")) is True
    assert ChainedAIClient._should_fallback(Exception("401 unauthorized")) is True
    assert ChainedAIClient._should_fallback(Exception("403 forbidden")) is True
    assert ChainedAIClient._should_fallback(Exception("quota exceeded")) is True
    assert ChainedAIClient._should_fallback(Exception("502 bad gateway")) is True
    assert ChainedAIClient._should_fallback(Exception("503 service unavailable")) is True
    assert ChainedAIClient._should_fallback(Exception("Empty response from provider")) is True
    assert ChainedAIClient._should_fallback(Exception("some random error")) is False


def test_lazy_initialization():
    """Downstream clients are not instantiated when the first provider succeeds."""
    cfg1 = _make_config(AIProvider.OPENAI)
    cfg2 = _make_config(AIProvider.OLLAMA)
    client1 = _DummyClient(result="ok")
    client2 = _DummyClient(result="also ok")

    factory = _MockFactory(client1, client2)
    chained = ChainedAIClient([cfg1, cfg2], client_factory=factory)
    result = asyncio.run(chained.complete("sys", "usr"))

    assert result == "ok"
    assert len(factory.calls) == 1
    assert factory.calls[0].provider == AIProvider.OPENAI


def test_create_chained_client_parses_chain():
    """_create_chained_client correctly parses provider chain string."""
    config = AIConfig(
        provider=AIProvider.OPENAI,
        model="m1",
        api_key_env="K1",
        provider_chain="openai,ollama",
    )
    chained = _create_chained_client(config)
    assert len(chained.configs) == 2
    assert chained.configs[0].provider == AIProvider.OPENAI
    assert chained.configs[1].provider == AIProvider.OLLAMA
    assert chained.configs[1].model == "llama3.1"
    assert chained.configs[1].api_key_env == ""


def test_create_chained_client_rejects_unknown_provider():
    """_create_chained_client rejects unknown providers in chain."""
    config = AIConfig(
        provider=AIProvider.OPENAI,
        model="m1",
        api_key_env="K1",
        provider_chain="openai,unknownprovider",
    )
    with pytest.raises(ValueError, match="Unsupported AI provider in chain"):
        _create_chained_client(config)
