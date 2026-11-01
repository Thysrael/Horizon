"""Parameter compatibility at the SDK HTTP boundary, without live credentials."""

import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
import json
from unittest.mock import patch

import anthropic
import httpx
import openai
import pytest

from src.ai.client import create_ai_client
from src.models import AIConfig


PROVIDERS = ["anthropic", "azure", "openai", "minimax", "deepseek", "ali", "doubao", "ollama"]
CHAT_PROVIDERS = PROVIDERS[1:]
TEMPERATURE_ERROR = "Unsupported value: 'temperature' does not support 0.3. Only the default (1) is supported."
TOKEN_ERROR = "Unsupported parameter: 'max_tokens'. Use 'max_completion_tokens' instead."


@pytest.fixture(autouse=True)
def credentials(monkeypatch):
    monkeypatch.setenv("PARAMETER_TEST_KEY", "offline-test-key")
    monkeypatch.setenv("PARAMETER_TEST_ENDPOINT", "https://example.openai.azure.com")


@asynccontextmanager
async def client_for(provider, handler, **overrides):
    config = AIConfig(
        **{
            "provider": provider, "model": "custom-deployment", "api_key_env": "PARAMETER_TEST_KEY",
            "azure_endpoint_env": "PARAMETER_TEST_ENDPOINT", "api_version": "2024-10-21",
            "temperature": 0.3, "max_tokens": 4096, **overrides,
        }
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as transport:
        options = {"api_key": "offline-test-key", "http_client": transport, "max_retries": 0}
        if provider == "anthropic":
            sdk_type = anthropic.AsyncAnthropic
        elif provider == "azure":
            sdk_type = openai.AsyncAzureOpenAI
            options.update(azure_endpoint="https://example.openai.azure.com", api_version=config.api_version)
        else:
            sdk_type = openai.AsyncOpenAI
        sdk = sdk_type(**options)
        with patch(f"src.ai.client.{sdk_type.__name__}", return_value=sdk):
            yield create_ai_client(config)


def success(provider):
    if provider == "anthropic":
        payload = {
            "id": "msg_test", "type": "message", "role": "assistant", "model": "test",
            "content": [{"type": "text", "text": "ok"}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 2, "output_tokens": 1},
        }
    else:
        payload = {
            "id": "chat_test", "object": "chat.completion", "created": 0, "model": "test",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": "ok",
            }}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
        }
    return httpx.Response(200, json=payload)


def failure(message, status=400):
    return httpx.Response(status, json={
        "type": "error", "error": {"type": "invalid_request_error", "message": message},
    })


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("override", [None, 0])
def test_temperature_rejection_is_retried_and_remembered(provider, override):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        return failure(TEMPERATURE_ERROR) if "temperature" in body else success(provider)

    async def run():
        # A configured temperature of 1 does not protect internal zero overrides.
        async with client_for(provider, handler, temperature=1 if override == 0 else 0.3) as client:
            assert await client.complete("system", "hello", temperature=override, max_tokens=1234) == "ok"
            assert await client.complete("system", "hello", temperature=0, max_tokens=1234) == "ok"

    asyncio.run(run())
    assert len(bodies) == 3
    expected = 0.01 if provider == "minimax" and override == 0 else (0.3 if override is None else 0)
    assert bodies[0].pop("temperature") == expected
    assert bodies[0] == bodies[1] == bodies[2]
    assert bodies[1]["max_tokens"] == 1234


@pytest.mark.parametrize("provider", ["anthropic", "azure", "openai"])
@pytest.mark.parametrize("message", [
    "`temperature` is deprecated for this model.",
    "temperature may only be set to 1 when thinking is enabled",
    "invalid temperature: only 1 is allowed for this model.",
])
def test_fixed_temperature_models_preserve_other_extra_fields(provider, message):
    bodies = []
    extra = {"temperature": 0.7, "thinking": {"type": "enabled", "budget_tokens": 1024}}
    original = deepcopy(extra)

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        return failure(message) if "temperature" in body else success(provider)

    async def run():
        async with client_for(provider, handler, extra_body=extra) as client:
            assert await client.complete("system", "hello") == "ok"
            assert await client.complete("system", "hello", temperature=0) == "ok"
            assert client.config.extra_body == original

    asyncio.run(run())
    assert len(bodies) == 3
    assert bodies[0].pop("temperature") == 0.7
    assert bodies[0] == bodies[1] == bodies[2]
    assert bodies[2]["thinking"] == original["thinking"]
    assert extra == original


@pytest.mark.parametrize("provider", CHAT_PROVIDERS)
@pytest.mark.parametrize("temperature_first", [False, True])
def test_token_and_temperature_fallbacks_combine_in_either_order(provider, temperature_first):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if temperature_first and "temperature" in body:
            return failure(TEMPERATURE_ERROR)
        if "max_tokens" in body:
            return failure(TOKEN_ERROR)
        if "temperature" in body:
            return failure(TEMPERATURE_ERROR)
        return success(provider)

    async def run():
        async with client_for(provider, handler, extra_body={"reasoning_effort": "high"}) as client:
            assert await client.complete("system", "hello", max_tokens=1234) == "ok"
            assert await client.complete("system", "hello", temperature=0, max_tokens=5678) == "ok"

    asyncio.run(run())
    assert len(bodies) == 4
    assert bodies[0]["max_tokens"] == 1234
    assert bodies[2]["max_completion_tokens"] == 1234
    assert bodies[3]["max_completion_tokens"] == 5678
    for body in bodies[2:]:
        assert "temperature" not in body
        assert "max_tokens" not in body
        assert body["reasoning_effort"] == "high"


@pytest.mark.parametrize("provider", ["azure", "openai"])
def test_compatible_endpoints_can_report_parameter_rejection_as_422(provider):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        return failure(TEMPERATURE_ERROR, 422) if "temperature" in body else success(provider)

    async def run():
        async with client_for(provider, handler) as client:
            assert await client.complete("system", "hello") == "ok"

    asyncio.run(run())
    assert len(bodies) == 2
    assert "temperature" not in bodies[1]


@pytest.mark.parametrize("provider", ["azure", "openai"])
@pytest.mark.parametrize("token_param", ["max_tokens", "max_completion_tokens"])
def test_token_override_in_extra_body_survives_parameter_switch(provider, token_param):
    bodies = []
    extra = {token_param: 2048, "temperature": 0.7, "reasoning_effort": "high"}
    original = deepcopy(extra)
    target_param = "max_completion_tokens" if token_param == "max_tokens" else "max_tokens"

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if token_param in body:
            return failure(f"Use '{target_param}' instead of the unsupported '{token_param}' parameter.")
        if "temperature" in body:
            return failure(TEMPERATURE_ERROR)
        return success(provider)

    async def run():
        model = "gpt-5-custom" if token_param == "max_completion_tokens" else "custom-deployment"
        async with client_for(provider, handler, model=model, extra_body=extra) as client:
            assert await client.complete("system", "hello") == "ok"
            assert await client.complete("system", "hello", temperature=0) == "ok"
            assert client.config.extra_body == original

    asyncio.run(run())
    assert len(bodies) == 4
    assert bodies[0][token_param] == 2048
    assert bodies[1][target_param] == 2048
    assert bodies[2] == bodies[3]
    assert bodies[3][target_param] == 2048
    assert token_param not in bodies[3]
    assert "temperature" not in bodies[3]
    assert bodies[3]["reasoning_effort"] == "high"
    assert extra == original


@pytest.mark.parametrize("provider", ["azure", "openai"])
def test_wrong_token_guess_can_fall_back_to_legacy_parameter(provider):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if "max_completion_tokens" in body:
            return failure("Unsupported parameter: 'max_completion_tokens'. Use 'max_tokens' instead.")
        return success(provider)

    async def run():
        async with client_for(provider, handler, model="gpt-5-custom-proxy") as client:
            assert await client.complete("system", "hello") == "ok"
            assert await client.complete("system", "hello") == "ok"

    asyncio.run(run())
    assert len(bodies) == 3
    assert bodies[0]["max_completion_tokens"] == 4096
    assert bodies[1] == bodies[2]
    assert bodies[1]["max_tokens"] == 4096
    assert "max_completion_tokens" not in bodies[1]
    assert bodies[1]["temperature"] == 0.3


@pytest.mark.parametrize("provider", ["anthropic", "azure", "openai"])
@pytest.mark.parametrize("status,message", [
    (400, "temperature must be between 0 and 1"),
    (400, "Unsupported parameter: top_p"),
    (400, "max_tokens exceeds the context window"),
    (401, "temperature is unsupported; authentication failed"),
    (429, "temperature is unsupported; rate limit exceeded"),
    (500, "temperature is unsupported; service unavailable"),
])
def test_unrelated_errors_are_not_retried_or_remembered(provider, status, message):
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return failure(message, status) if len(bodies) == 1 else success(provider)

    async def run():
        async with client_for(provider, handler, model="gpt-5-custom") as client:
            with pytest.raises((anthropic.APIStatusError, openai.APIStatusError)) as caught:
                await client.complete("system", "hello")
            assert caught.value.status_code == status
            assert len(bodies) == 1
            assert await client.complete("system", "hello") == "ok"

    asyncio.run(run())
    assert bodies[0] == bodies[1]


@pytest.mark.parametrize("provider", ["anthropic", "azure", "openai"])
def test_temperature_retry_failure_is_propagated(provider):
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return failure(TEMPERATURE_ERROR)

    async def run():
        async with client_for(provider, handler) as client:
            with pytest.raises((anthropic.BadRequestError, openai.BadRequestError)):
                await client.complete("system", "hello")

    asyncio.run(run())
    assert len(bodies) == 2
    assert "temperature" not in bodies[1]


@pytest.mark.parametrize("provider", ["azure", "openai"])
def test_conflicting_token_rejections_do_not_loop(provider):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if "temperature" in body:
            return failure(TEMPERATURE_ERROR)
        if "max_tokens" in body:
            return failure(TOKEN_ERROR)
        return failure("Unsupported parameter: 'max_completion_tokens'. Use 'max_tokens' instead.")

    async def run():
        async with client_for(provider, handler) as client:
            with pytest.raises(openai.BadRequestError):
                await client.complete("system", "hello")

    asyncio.run(run())
    assert len(bodies) == 3


@pytest.mark.parametrize("provider", PROVIDERS)
def test_compatible_models_keep_temperature_without_retry(provider):
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return success(provider)

    async def run():
        async with client_for(provider, handler) as client:
            assert await client.complete("system", "hello") == "ok"
            assert await client.complete("system", "hello", temperature=0) == "ok"

    asyncio.run(run())
    assert len(bodies) == 2
    assert bodies[0]["temperature"] == 0.3
    assert bodies[1]["temperature"] == (0.01 if provider == "minimax" else 0)
