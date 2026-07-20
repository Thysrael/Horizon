"""Tests for ChainedAIClient fallback logic."""

import asyncio
from datetime import datetime, timezone

import pytest

from src.ai.client import ChainedAIClient, _create_chained_client
from src.models import AIConfig, AIProvider, AI_PROVIDER_DEFAULTS


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


def test_create_chained_client_rejects_runtime_key():
    config = AIConfig(
        provider=AIProvider.OPENAI,
        model="m1",
        api_key_env="K1",
        provider_chain="openai,ollama",
    )

    with pytest.raises(ValueError, match="provider chains"):
        _create_chained_client(config, api_key="sk-user")


def test_create_chained_client_uses_provider_defaults_without_leaking_base_url():
    """Every heterogeneous entry gets its own connection defaults."""
    providers = list(AIProvider)
    config = AIConfig(
        provider=AIProvider.OPENAI,
        provider_chain=",".join(provider.value for provider in providers),
        model="custom-primary-model",
        api_key_env="CUSTOM_PRIMARY_API_KEY",
        base_url="https://primary.example/v1",
        temperature=0.17,
        max_tokens=1234,
        throttle_sec=0.75,
        analysis_concurrency=3,
        enrichment_concurrency=5,
        languages=["en", "zh-CN"],
    )

    chained = _create_chained_client(config)

    assert [entry.provider for entry in chained.configs] == providers
    for entry in chained.configs:
        defaults = AI_PROVIDER_DEFAULTS[entry.provider]
        assert entry.model == defaults["model"]
        assert entry.api_key_env == defaults["api_key_env"]
        expected_base_url = (
            config.base_url
            if entry.provider == config.provider
            else defaults["base_url"]
        )
        assert entry.base_url == expected_base_url
        assert entry.temperature == config.temperature
        assert entry.max_tokens == config.max_tokens
        assert entry.throttle_sec == config.throttle_sec
        assert entry.analysis_concurrency == config.analysis_concurrency
        assert entry.enrichment_concurrency == config.enrichment_concurrency
        assert entry.languages == config.languages


def test_create_chained_client_preserves_custom_azure_and_common_settings():
    config = AIConfig(
        provider=AIProvider.AZURE,
        provider_chain="azure,openai",
        model="custom-deployment",
        api_key_env="CUSTOM_AZURE_API_KEY",
        base_url="https://unused-azure-base.example",
        azure_endpoint_env="CUSTOM_AZURE_ENDPOINT",
        api_version="2025-01-01-preview",
        temperature=0.42,
        max_tokens=2048,
        throttle_sec=1.25,
        analysis_concurrency=4,
        enrichment_concurrency=6,
        languages=["ja", "en-US"],
    )

    azure, openai = _create_chained_client(config).configs

    assert azure.azure_endpoint_env == "CUSTOM_AZURE_ENDPOINT"
    assert azure.api_version == "2025-01-01-preview"
    assert openai.azure_endpoint_env is None
    assert openai.api_version is None
    for entry in (azure, openai):
        assert entry.temperature == 0.42
        assert entry.max_tokens == 2048
        assert entry.throttle_sec == 1.25
        assert entry.analysis_concurrency == 4
        assert entry.enrichment_concurrency == 6
        assert entry.languages == ["ja", "en-US"]


def test_create_chained_client_applies_azure_connection_defaults():
    config = AIConfig(
        provider=AIProvider.OPENAI,
        provider_chain="openai,azure",
        model="m1",
        api_key_env="K1",
    )

    azure = _create_chained_client(config).configs[1]

    assert azure.azure_endpoint_env == "AZURE_OPENAI_ENDPOINT"
    assert azure.api_version == "2024-10-21"


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
