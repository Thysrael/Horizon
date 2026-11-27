"""AI/ML API provider: defaults, key host guard and setup wizard behavior."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from src.ai.client import OpenAIClient, _create_single_client, _missing_api_key_message
from src.models import AI_PROVIDER_DEFAULTS, AIConfig, AIProvider
from src.setup import wizard
from src.storage.manager import StorageManager

TEST_KEY = "test-aimlapi-key"


def _aimlapi_config(**overrides) -> AIConfig:
    values = {
        "provider": AIProvider.AIMLAPI,
        "model": "openai/gpt-4.1-mini",
        "api_key_env": "AIMLAPI_API_KEY",
    }
    values.update(overrides)
    return AIConfig(**values)


def _chat_response(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": "openai/gpt-4.1-mini",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": '{"ok": true}'},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
    )


def test_aimlapi_defaults():
    defaults = AI_PROVIDER_DEFAULTS[AIProvider.AIMLAPI]
    assert defaults["base_url"] == "https://api.aimlapi.com/v1"
    assert defaults["api_key_env"] == "AIMLAPI_API_KEY"
    assert defaults["model"] == "openai/gpt-4.1-mini"


def test_aimlapi_uses_openai_compatible_client(monkeypatch):
    monkeypatch.setenv("AIMLAPI_API_KEY", TEST_KEY)

    client = _create_single_client(_aimlapi_config())

    assert isinstance(client, OpenAIClient)
    assert str(client.client.base_url) == "https://api.aimlapi.com/v1/"
    assert client.client.api_key == TEST_KEY


def test_missing_aimlapi_key_names_its_variable():
    message = _missing_api_key_message(_aimlapi_config(api_key_env="MISSING_AIMLAPI_KEY"))
    assert "AIMLAPI_API_KEY" in message


@pytest.mark.parametrize(
    "base_url",
    [
        "https://example.com/v1",
        "https://api.aimlapi.com.example.com/v1",
        "https://evil-api.aimlapi.com/v1",
        "http://api.aimlapi.com/v1",
        "https://api.aimlapi.com:8443/v1",
    ],
)
def test_aimlapi_key_is_not_sent_to_other_hosts(monkeypatch, base_url):
    monkeypatch.setenv("AIMLAPI_API_KEY", TEST_KEY)

    with pytest.raises(ValueError, match="api.aimlapi.com"):
        _create_single_client(_aimlapi_config(base_url=base_url))


def test_other_providers_keep_custom_base_url(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    config = AIConfig(
        provider=AIProvider.OPENAI,
        model="gpt-4",
        api_key_env="OPENAI_API_KEY",
        base_url="https://proxy.example.com/v1",
    )

    client = _create_single_client(config)

    assert str(client.client.base_url) == "https://proxy.example.com/v1/"


def test_key_reaches_aimlapi_and_is_dropped_on_cross_host_redirect(monkeypatch):
    monkeypatch.setenv("AIMLAPI_API_KEY", TEST_KEY)
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.host, request.headers.get("authorization")))
        if request.url.host == "api.aimlapi.com":
            return httpx.Response(
                307, headers={"location": "https://collector.example.com/v1/chat/completions"}
            )
        return _chat_response(request)

    client = OpenAIClient(_aimlapi_config())
    client.client = client.client.with_options(max_retries=0)
    client.client._client._transport = httpx.MockTransport(handler)

    asyncio.run(client.complete(system="s", user="u"))

    assert seen[0] == ("api.aimlapi.com", f"Bearer {TEST_KEY}")
    assert [host for host, _ in seen] == ["api.aimlapi.com", "collector.example.com"]
    leaked = [auth for host, auth in seen if host != "api.aimlapi.com" and auth]
    assert leaked == []


def _answer_with_defaults(monkeypatch, overrides=None):
    """Answer every wizard prompt with its default unless overridden by label."""
    overrides = overrides or {}
    asked = []

    def ask(label, *args, **kwargs):
        asked.append((label, kwargs.get("default")))
        if label in overrides:
            return overrides[label]
        return kwargs.get("default")

    printed = []
    monkeypatch.setattr(wizard.Prompt, "ask", ask)
    monkeypatch.setattr(wizard, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(
        wizard.console, "print", lambda *args, **kwargs: printed.append(" ".join(map(str, args)))
    )
    return asked, printed


def _clear_provider_keys(monkeypatch):
    for defaults in AI_PROVIDER_DEFAULTS.values():
        if defaults.get("api_key_env"):
            monkeypatch.delenv(defaults["api_key_env"], raising=False)


def test_wizard_links_aimlapi_keys(monkeypatch):
    _clear_provider_keys(monkeypatch)
    _, printed = _answer_with_defaults(monkeypatch, {"AI provider": "aimlapi"})

    config = wizard.configure_ai()

    assert config.provider == AIProvider.AIMLAPI
    assert config.model == "openai/gpt-4.1-mini"
    assert config.api_key_env == "AIMLAPI_API_KEY"
    assert config.base_url is None
    assert any("https://aimlapi.com/app/keys" in line for line in printed)


def test_rerunning_wizard_keeps_existing_ai_config(monkeypatch):
    _clear_provider_keys(monkeypatch)
    existing = AIConfig(
        provider=AIProvider.DEEPSEEK,
        provider_chain="deepseek,openai",
        model="deepseek-reasoner",
        base_url="https://api.deepseek.com",
        api_key_env="MY_DEEPSEEK_KEY",
        extra_body={"thinking": {"type": "enabled"}},
        temperature=0.1,
        max_tokens=2048,
        languages=["en"],
    )
    asked, _ = _answer_with_defaults(monkeypatch)

    config = wizard.configure_ai(existing)

    assert asked[0] == ("AI provider", "deepseek")
    assert config == existing


def test_wizard_main_reads_existing_ai_config(tmp_path):
    config_path = tmp_path / "config.json"
    saved = AIConfig(provider=AIProvider.DEEPSEEK, model="deepseek-chat", api_key_env="DEEPSEEK_API_KEY")
    storage = StorageManager(data_dir=str(tmp_path), config_path=str(config_path))
    storage.save_config(wizard.build_config(saved, []))

    existing = wizard._existing_ai_config(storage)

    assert existing == saved
    assert wizard._existing_ai_config(
        StorageManager(data_dir=str(tmp_path), config_path=str(tmp_path / "missing.json"))
    ) is None
