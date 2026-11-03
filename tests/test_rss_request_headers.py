from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx

from src.models import RSSSourceConfig
from src.scrapers.rss import RSSScraper


_FEED = """<rss version="2.0"><channel><title>Publisher AI</title>
<item><guid>release-1</guid><title>Model update</title>
<link>https://publisher.example/model-update</link>
<pubDate>Mon, 02 Nov 2026 09:00:00 GMT</pubDate>
<description>Original publisher summary.</description></item>
</channel></rss>"""
_SINCE = datetime(2026, 11, 2, tzinfo=timezone.utc)


def test_feed_publisher_rejecting_httpx_default_user_agent_is_readable():
    requests = []

    def respond(request):
        requests.append(request)
        if request.headers.get("User-Agent", "").startswith("python-httpx/"):
            return httpx.Response(403, text="Forbidden")
        return httpx.Response(200, text=_FEED)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            url = "https://publisher.example/ai/feed/"
            assert (await client.get(url)).status_code == 403
            result = await RSSScraper([RSSSourceConfig(name="AI", url=url)], client).fetch(_SINCE)
            return result

    result = asyncio.run(run())
    assert result.status == "success"
    assert result.successful == 1
    assert not result.failures
    assert len(result.items) == 1
    assert result.items[0].title == "Model update"
    assert result.items[0].content == "Original publisher summary."
    assert result.items[0].published_at == datetime(2026, 11, 2, 9, tzinfo=timezone.utc)
    assert "Horizon" in requests[1].headers["User-Agent"]


def test_reader_identity_does_not_mutate_shared_client_or_drop_other_headers():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, text=_FEED)

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(respond),
            headers={"X-Request-Context": "shared-client"},
        ) as client:
            original_headers = dict(client.headers)
            result = await RSSScraper([
                RSSSourceConfig(name="AI", url="https://publisher.example/feed/")
            ], client).fetch(_SINCE)
            assert dict(client.headers) == original_headers
            await client.get("https://publisher.example/article")
            return result

    assert asyncio.run(run()).status == "success"
    assert requests[0].headers["X-Request-Context"] == "shared-client"
    assert "Horizon" in requests[0].headers["User-Agent"]
    assert requests[1].headers["User-Agent"].startswith("python-httpx/")


def test_real_forbidden_response_is_reported_as_failure():
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(403, text="Forbidden")
        )) as client:
            return await RSSScraper([
                RSSSourceConfig(name="Blocked", url="https://publisher.example/feed/")
            ], client).fetch(_SINCE)

    result = asyncio.run(run())
    assert result.status == "failure"
    assert not result.items
    assert result.successful == 0
    assert "Blocked" in result.failures
    assert "403" in result.failures["Blocked"]
