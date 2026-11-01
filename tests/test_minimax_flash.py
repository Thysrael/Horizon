"""Exercise MiniMax defaults and preserved model choices at the SDK HTTP boundary."""

import asyncio
import json
from unittest.mock import patch

import httpx
import pytest
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from src.ai.client import create_ai_client
from src.models import AIConfig, AIProvider
from src.setup import wizard


@pytest.mark.parametrize("region", [
    "api.minimax.io", "api.minimax.cn", "api.minimaxi.com", "proxy.example",
])
@pytest.mark.parametrize("protocol", ["v1", "anthropic"])
@pytest.mark.parametrize("model", [None, "MiniMax-M3", "MiniMax-M2.7", "custom-model"])
@pytest.mark.parametrize("chained", [False, True])
def test_setup_and_saved_models_reach_http(monkeypatch, region, protocol, model, chained):
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setattr(wizard, "load_dotenv", lambda: None)
    base_url = f"https://{region}/{protocol}"

    def answer_prompt(prompt, **kwargs):
        answers = {
            "AI provider": "minimax",
            "Model name": model or kwargs["default"],
            "Base URL (leave empty for default)": base_url,
        }
        return answers.get(prompt, kwargs["default"])

    monkeypatch.setattr(wizard.Prompt, "ask", answer_prompt)
    config = wizard.configure_ai()
    # Persist and reload through the same model used for saved configuration.
    config = AIConfig.model_validate_json(config.model_dump_json())
    if chained:
        config.provider_chain = "minimax,openai"
    expected_model = model or "MiniMax-M3.1-Flash"
    requests = []

    def handler(request):
        requests.append(request)
        if protocol == "anthropic":
            response = {
                "id": "msg_test", "type": "message", "role": "assistant",
                "model": expected_model,
                "content": [
                    {"type": "thinking", "thinking": "private reasoning", "signature": "test"},
                    {"type": "text", "text": "{\"ok\":"},
                    {"type": "text", "text": "true}"},
                ],
                "stop_reason": "end_turn", "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        else:
            response = {
                "id": "chat_test", "object": "chat.completion", "created": 0,
                "model": expected_model,
                "choices": [{"index": 0, "finish_reason": "stop", "message": {
                    "role": "assistant", "content": '{"ok":true}',
                    "reasoning_content": "private reasoning",
                }}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        return httpx.Response(200, json=response)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as transport:
            sdk_type = AsyncAnthropic if protocol == "anthropic" else AsyncOpenAI
            sdk = sdk_type(api_key="test-key", base_url=base_url, http_client=transport)
            with patch(f"src.ai.client.{sdk_type.__name__}", return_value=sdk):
                client = create_ai_client(config)
                assert await client.complete("system", "hello") == '{"ok":true}'

    asyncio.run(run())
    assert len(requests) == 1
    request = requests[0]
    suffix = "/v1/messages" if protocol == "anthropic" else "/chat/completions"
    assert str(request.url) == base_url + suffix
    body = json.loads(request.content)
    assert body["model"] == expected_model
    assert body["max_tokens"] == 8192
    assert body["temperature"] == 0.3
    assert body["messages"][-1] == {"role": "user", "content": "hello"}
    # Omission preserves Flash's adaptive/max defaults and legacy API behavior.
    for key in ("thinking", "reasoning_effort", "output_config", "service_tier",
                "reasoning_split", "tools", "previous_response_id"):
        assert key not in body


@pytest.mark.parametrize("protocol", ["v1", "anthropic"])
def test_existing_image_content_passthrough(monkeypatch, protocol):
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    base_url = f"https://api.minimax.io/{protocol}"
    image = (
        {"type": "image", "source": {"type": "url", "url": "https://example.com/image.png"}}
        if protocol == "anthropic" else
        {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}}
    )
    content = [{"type": "text", "text": "Describe this image"}, image]
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        if protocol == "anthropic":
            response = {
                "id": "msg_test", "type": "message", "role": "assistant",
                "model": "MiniMax-M3.1-Flash", "content": [{"type": "text", "text": "ok"}],
                "stop_reason": "end_turn", "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        else:
            response = {
                "id": "chat_test", "object": "chat.completion", "created": 0,
                "model": "MiniMax-M3.1-Flash",
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "ok"}}],
            }
        return httpx.Response(200, json=response)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as transport:
            sdk_type = AsyncAnthropic if protocol == "anthropic" else AsyncOpenAI
            sdk = sdk_type(api_key="test-key", base_url=base_url, http_client=transport)
            with patch(f"src.ai.client.{sdk_type.__name__}", return_value=sdk):
                client = create_ai_client(AIConfig(
                    provider="minimax", model="MiniMax-M3.1-Flash",
                    api_key_env="MINIMAX_API_KEY", base_url=base_url,
                ))
                assert await client.complete("system", content) == "ok"

    asyncio.run(run())
    assert requests[0]["messages"][-1]["content"] == content


def test_fallback_uses_flash_without_changing_primary_provider(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    config = AIConfig(provider="openai", model="gpt-4", api_key_env="OPENAI_API_KEY",
                      provider_chain="openai,minimax")
    client = create_ai_client(config)
    assert client.configs[0].provider == AIProvider.OPENAI
    assert client.configs[0].model == "gpt-4"
    assert client.configs[1].model == "MiniMax-M3.1-Flash"
    assert client.configs[1].base_url == "https://api.minimax.io/v1"
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={
            "id": "chat_test", "object": "chat.completion", "created": 0,
            "model": "MiniMax-M3.1-Flash",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": "ok"}}],
        })

    class UnavailablePrimary:
        async def complete(self, *args):
            raise RuntimeError("503 service unavailable")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as transport:
            sdk = AsyncOpenAI(api_key="test-key", base_url="https://api.minimax.io/v1",
                              http_client=transport)
            with patch("src.ai.client.AsyncOpenAI", return_value=sdk):
                client._client_cache[0] = UnavailablePrimary()
                assert await client.complete("system", "hello") == "ok"

    asyncio.run(run())
    assert str(requests[0].url) == "https://api.minimax.io/v1/chat/completions"
    assert json.loads(requests[0].content)["model"] == "MiniMax-M3.1-Flash"
