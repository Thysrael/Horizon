from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from src.models import RSSSourceConfig
from src.scrapers import rss
from src.scrapers.rss import RSSScraper


_FEED = """<rss version="2.0"><channel><title>Community</title>
<item><guid>post-1</guid><title>New open-weight model</title>
<link>https://community.example/post-1</link>
<pubDate>Mon, 02 Nov 2026 09:00:00 GMT</pubDate>
<description>Discussion of a release.</description></item>
</channel></rss>"""
_SINCE = datetime(2026, 11, 2, tzinfo=timezone.utc)
_URL = "https://community.example/top/.rss"


@pytest.fixture
def sleeps(monkeypatch):
    waited = []

    async def fake_sleep(seconds):
        waited.append(seconds)

    monkeypatch.setattr(rss.asyncio, "sleep", fake_sleep)
    return waited


def _fetch(respond):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            return await RSSScraper([RSSSourceConfig(name="Community", url=_URL)], client).fetch(_SINCE)

    return asyncio.run(run())


def test_rate_limited_feed_is_retried_until_it_succeeds(sleeps):
    responses = iter([httpx.Response(429), httpx.Response(429), httpx.Response(200, text=_FEED)])
    result = _fetch(lambda request: next(responses))

    assert result.status == "success"
    assert [item.title for item in result.items] == ["New open-weight model"]
    assert sleeps == [rss.RATE_LIMIT_BACKOFF_SEC, rss.RATE_LIMIT_BACKOFF_SEC * 2]


def test_numeric_retry_after_is_honoured_and_capped(sleeps):
    responses = iter([
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(429, headers={"Retry-After": "3600"}),
        httpx.Response(200, text=_FEED),
    ])
    result = _fetch(lambda request: next(responses))

    assert result.status == "success"
    assert sleeps == [7.0, rss.RATE_LIMIT_MAX_WAIT_SEC]


def test_feed_still_rate_limited_after_retries_is_reported_as_failure(sleeps):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(429)

    result = _fetch(respond)

    assert result.status == "failure"
    assert "429" in result.failures["Community"]
    assert len(calls) == rss.RATE_LIMIT_RETRIES + 1
    assert len(sleeps) == rss.RATE_LIMIT_RETRIES


def test_other_errors_are_not_retried(sleeps):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(403)

    result = _fetch(respond)

    assert result.status == "failure"
    assert len(calls) == 1
    assert sleeps == []
