"""Exercise the actual OpenAI SDK's Responses request and SSE parsing offline."""

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from src.ai.chatgpt import ChatGPTClient
from src.ai.client import ChainedAIClient, _create_chained_client
from src.ai.errors import AIProviderUnavailableError
from src.models import AIConfig


def response(status="completed", text='{"ok": true}', error=None):
    return {
        "id": "resp_test", "object": "response", "created_at": 1, "model": "plan-model",
        "status": status, "error": error,
        "output": [{
            "id": "msg_test", "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": text, "annotations": []}],
        }] if status == "completed" else [],
        "usage": {"input_tokens": 5, "output_tokens": 3, "total_tokens": 8,
                  "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}},
    }


def sse(*events):
    return "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events)


DELTA = {"type": "response.output_text.delta", "delta": '{"ok": true}', "sequence_number": 1,
         "item_id": "msg_test", "output_index": 0, "content_index": 0, "logprobs": []}


def make_client():
    auth = SimpleNamespace(
        status=lambda account: {"connected": True, "plan_usage": True, "client_id": "oaiapp_test"},
        access_token=Mock(return_value="access-secret"),
    )
    return ChatGPTClient(AIConfig(provider="openai-chatgpt", model="plan-model"), auth=auth)


async def attach_transport(client, handler):
    original = client.client
    client.client = original.with_options(http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    await original.close()


def test_responses_wire_protocol_and_terminal_text(monkeypatch, caplog):
    caplog.set_level("DEBUG")
    requests, usages = [], []
    monkeypatch.setattr("src.ai.chatgpt.record_usage", lambda provider, **usage: usages.append((provider, usage)))

    def handle(request):
        requests.append(request)
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text=sse(
            {**DELTA, "delta": '{"partial": true}'},
            {"type": "response.completed", "sequence_number": 2, "response": response()},
        ))

    async def run():
        client = make_client()
        await attach_transport(client, handle)
        try:
            assert json.loads(await client.complete("Return JSON.", "Check.", temperature=0, max_tokens=5)) == {"ok": True}
        finally:
            await client.client.close()

    asyncio.run(run())
    assert len(requests) == 1
    request = requests[0]
    assert str(request.url) == "https://api.openai.com/v1/responses"
    assert request.headers["authorization"] == "Bearer access-secret"
    assert json.loads(request.content) == {
        "model": "plan-model", "instructions": "Return JSON.",
        "input": [{"role": "user", "content": "Check."}], "store": False, "stream": True,
    }
    assert usages == [("openai-chatgpt", {"input_tokens": 5, "output_tokens": 3})]
    assert "access-secret" not in caplog.text


@pytest.mark.parametrize("terminal", [None, "response.incomplete", "response.failed", "error"])
def test_partial_json_is_never_a_success_without_completed(terminal):
    events = [DELTA]
    if terminal in {"response.failed", "response.incomplete"}:
        events.append({"type": terminal, "sequence_number": 2, "response": response(
            status=terminal.split(".")[1], error={"code": "server_error", "message": "secret-response"},
        )})
    elif terminal == "error":
        events.append({"type": "error", "sequence_number": 2, "code": "server_error", "message": "secret-response", "param": None})

    async def run():
        client = make_client()
        await attach_transport(client, lambda _: httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, text=sse(*events),
        ))
        try:
            with pytest.raises(RuntimeError) as error:
                await client.complete("s", "u")
            assert "secret-response" not in str(error.value)
        finally:
            await client.client.close()

    asyncio.run(run())


@pytest.mark.parametrize("error_kind", ["response.failed", "error", "sdk_error"])
def test_streamed_usage_limit_blocks_future_requests(error_kind):
    requests = []
    error = {"code": "subscription_sharing_usage_limit_exceeded", "message": "secret-response"}
    if error_kind == "response.failed":
        event = {"type": "response.failed", "sequence_number": 2, "response": response(status="failed", error=error)}
    elif error_kind == "error":
        event = {"type": "error", "sequence_number": 2, **error, "param": None}
    else:
        event = {"type": "error", "error": error}

    def handle(request):
        requests.append(request)
        return httpx.Response(200, headers={"Content-Type": "text/event-stream", "x-request-id": "req_stream"}, text=sse(DELTA, event))

    async def run():
        client = make_client()
        await attach_transport(client, handle)
        try:
            for _ in range(2):
                with pytest.raises(AIProviderUnavailableError, match="Manage usage") as error:
                    await client.complete("s", "u")
                assert "secret-response" not in str(error.value)
                assert "req_stream" in str(error.value)
            assert client.auth.access_token.call_count == 1
        finally:
            await client.client.close()

    asyncio.run(run())
    assert len(requests) == 1


@pytest.mark.parametrize("status,body", [
    (401, {"detail": "sensitive identity failure access-secret"}),
    (403, {"error": {"code": "subscription_sharing_user_not_eligible", "message": "access-secret"}}),
    (400, {"error": {"code": "subscription_sharing_unsupported_capability", "message": "access-secret"}}),
])
def test_admission_failures_stop_without_leaking_body(status, body):
    async def run():
        client = make_client()
        await attach_transport(client, lambda _: httpx.Response(status, json=body, headers={"x-request-id": "req_test"}))
        try:
            with pytest.raises(AIProviderUnavailableError) as error:
                await client.complete("s", "u")
            assert f"HTTP {status}" in str(error.value)
            assert "req_test" in str(error.value)
            assert "access-secret" not in str(error.value)
        finally:
            await client.client.close()
    asyncio.run(run())


def test_transient_service_failure_can_be_retried():
    requests = []

    def handle(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503, json={"error": {"code": "subscription_sharing_usage_unavailable"}})
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text=sse(
            {"type": "response.completed", "sequence_number": 1, "response": response()},
        ))

    async def run():
        client = make_client()
        await attach_transport(client, handle)
        try:
            with pytest.raises(RuntimeError, match="usage_unavailable") as error:
                await client.complete("s", "u")
            assert not isinstance(error.value, AIProviderUnavailableError)
            assert json.loads(await client.complete("s", "u")) == {"ok": True}
        finally:
            await client.client.close()
    asyncio.run(run())
    assert len(requests) == 2


def test_chatgpt_chain_preserves_selected_model_account_and_no_api_key():
    config = AIConfig(provider="openai-chatgpt", model="account-model", chatgpt_account="oaiapp_test", provider_chain="openai-chatgpt,openai")
    chatgpt, openai = _create_chained_client(config).configs
    assert chatgpt.model == "account-model"
    assert chatgpt.chatgpt_account == "oaiapp_test"
    assert chatgpt.api_key_env == ""
    assert openai.chatgpt_account is None


def test_plan_limits_do_not_fall_back_to_a_different_billing_path():
    assert not ChainedAIClient._should_fallback(AIProviderUnavailableError("429 usage limit exceeded"))
    assert ChainedAIClient._should_fallback(RuntimeError("503 temporary failure"))


@pytest.mark.parametrize("overrides", [
    {"base_url": "https://proxy.example/v1"}, {"extra_body": {"stream": False}},
    {"model": ""}, {"api_key_env": "OPENAI_API_KEY"},
])
def test_chatgpt_config_rejects_incompatible_request_settings(overrides):
    with pytest.raises(ValueError):
        AIConfig(**{"provider": "openai-chatgpt", "model": "account-model", **overrides})


def test_chatgpt_drives_classification_scoring_enrichment_and_digest(tmp_path, monkeypatch):
    from src.ai.summarizer import DailySummarizer
    from src.models import Config, ContentItem, SourceType
    from src.orchestrator import HorizonOrchestrator
    from src.processing import ProfileRegistry
    from src.storage.manager import StorageManager

    profiles = ProfileRegistry.load(Path(__file__).resolve().parents[1] / "profiles", "tech-news")
    replies = iter([
        {"profile": "tech-blog", "confidence": 0.95, "reason": "Engineering article"},
        {"score": 8, "reason": "Useful engineering details", "summary": "An architecture article.", "tags": ["systems"]},
        {"title": "A useful architecture", "blocks": [
            {"id": name, "type": "section", "title": name.title(), "content": f"Details about {name}.", "source_refs": []}
            for name in ("background", "solution", "takeaway")
        ]},
    ])
    requests = []

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text=sse({
            "type": "response.completed", "sequence_number": 1,
            "response": response(text=json.dumps(next(replies))),
        }))

    async def run():
        client = make_client()
        client.config.languages = ["en"]
        factory = Mock(return_value=client)
        monkeypatch.setattr("src.orchestrator.create_ai_client", factory)
        await attach_transport(client, handle)
        try:
            orchestrator = HorizonOrchestrator(
                Config(ai=client.config, sources={}), StorageManager(data_dir=tmp_path), profiles=profiles,
            )
            item = ContentItem(
                id="rss:article", source_type=SourceType.RSS, title="Architecture article",
                url="https://example.com/article", content="Design details.",
                published_at=datetime.now(timezone.utc), profile="auto",
            )
            await orchestrator.analyze_items([item])
            assert item.processing.classification.profile == "tech-blog"
            assert item.processing.analysis.score == 8
            result = await orchestrator.enrich_items([item])
            assert result.succeeded_ids == [item.id]
            assert factory.call_count == 1
            digest = await DailySummarizer(profile_names=profiles.names).generate_summary(
                [item], "2026-10-22", 1, language="en",
            )
            assert "A useful architecture" in digest
            assert "https://example.com/article" in digest
        finally:
            await client.client.close()

    asyncio.run(run())
    assert len(requests) == 3
    assert all("temperature" not in request and request["store"] is False for request in requests)


@pytest.mark.parametrize("stage", ["analysis", "enrichment"])
@pytest.mark.parametrize("concurrency", [1, 2])
def test_plan_exhaustion_stops_batch_without_per_item_retries(stage, concurrency, monkeypatch):
    from src.ai.analyzer import ContentAnalyzer
    from src.ai.enricher import ContentEnricher
    from src.models import ClassificationResult, ContentAnalysis, ContentItem, ProcessingResult, SourceType
    from src.processing import ProfileRegistry

    profiles = ProfileRegistry.load(Path(__file__).resolve().parents[1] / "profiles", "tech-news")
    requests = []
    sleeps = []
    cancelled = []

    async def retry_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(ContentAnalyzer._analyze_item.retry, "sleep", retry_sleep)
    monkeypatch.setattr(ContentEnricher._complete.retry, "sleep", retry_sleep)

    async def run():
        second_started = asyncio.Event()

        async def handle(request):
            requests.append(request)
            if concurrency > 1:
                if len(requests) == 1:
                    await second_started.wait()
                else:
                    second_started.set()
                    try:
                        await asyncio.Future()
                    except asyncio.CancelledError:
                        cancelled.append(request)
                        raise
            return httpx.Response(429, json={"error": {"code": "subscription_sharing_usage_limit_exceeded"}})

        client = make_client()
        await attach_transport(client, handle)
        items = [ContentItem(
            id=f"rss:article:{i}", source_type=SourceType.RSS, title="Architecture article",
            url=f"https://example.com/article/{i}", published_at=datetime.now(timezone.utc), profile="auto",
        ) for i in range(20)]
        try:
            if stage == "analysis":
                with pytest.raises(AIProviderUnavailableError):
                    await asyncio.wait_for(ContentAnalyzer(client, profiles, concurrency=concurrency).analyze_batch(items), 5)
            else:
                for item in items:
                    item.processing = ProcessingResult(
                        classification=ClassificationResult(profile="tech-blog", method="source_override"),
                        analysis=ContentAnalysis(score=8, reason="Useful", summary="Architecture."),
                    )
                with pytest.raises(AIProviderUnavailableError):
                    await asyncio.wait_for(ContentEnricher(client, profiles, ["en"], concurrency=concurrency).enrich_batch(items), 5)
            assert len(requests) == concurrency
            assert len(cancelled) == concurrency - 1
            assert sleeps == []
        finally:
            await client.client.close()

    asyncio.run(run())


@pytest.mark.parametrize("terminal", [response(text=""), response(status="failed")])
def test_empty_or_invalid_terminal_response_never_uses_partial_json(terminal):
    async def run():
        client = make_client()
        await attach_transport(client, lambda _: httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, text=sse(
                DELTA, {"type": "response.completed", "sequence_number": 2, "response": terminal},
            ),
        ))
        try:
            with pytest.raises(RuntimeError):
                await client.complete("s", "u")
        finally:
            await client.client.close()

    asyncio.run(run())


def test_interrupted_stream_discards_text_and_closes_connection():
    class InterruptedStream(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self):
            yield sse(DELTA).encode()
            raise httpx.ReadError("access-secret")

        async def aclose(self):
            self.closed = True

    stream = InterruptedStream()

    async def run():
        client = make_client()
        await attach_transport(client, lambda _: httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, stream=stream,
        ))
        try:
            with pytest.raises(RuntimeError, match="partial output was discarded") as error:
                await client.complete("s", "u")
            assert "access-secret" not in str(error.value)
            assert stream.closed
        finally:
            await client.client.close()

    asyncio.run(run())
