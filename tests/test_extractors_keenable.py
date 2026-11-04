from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.extractors import ExtractorRegistry, KeenableExtractor
from src.extractors.keenable import KEENABLE_FETCH_URL, KEENABLE_PUBLIC_FETCH_URL
from src.models import KeenableExtractorConfig, RSSSourceConfig
from src.scrapers.rss import RSSScraper

URL = "https://example.com/article"


@pytest.fixture(autouse=True)
def _no_api_key(monkeypatch):
    monkeypatch.delenv("KEENABLE_API_KEY", raising=False)


def _extractor(**kwargs) -> KeenableExtractor:
    return KeenableExtractor(KeenableExtractorConfig(**kwargs))


def _client(payload=None, status: int = 200) -> AsyncMock:
    response = MagicMock()
    response.json.return_value = payload if payload is not None else {
        "url": URL,
        "title": "Title",
        "content": "# Title\n\nArticle text.",
        "description": "",
    }
    response.raise_for_status.return_value = None
    if status >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=str(status), request=MagicMock(), response=MagicMock()
        )
    client = AsyncMock()
    client.get.return_value = response
    return client


def test_returns_markdown_without_api_key():
    client = _client()
    result = asyncio.run(_extractor().extract(URL, client))
    assert result == "# Title\n\nArticle text."
    client.get.assert_awaited_once_with(
        KEENABLE_PUBLIC_FETCH_URL,
        params={"url": URL},
        headers={"X-Keenable-Title": "Horizon"},
    )


def test_uses_keyed_endpoint_when_api_key_is_set(monkeypatch):
    monkeypatch.setenv("KEENABLE_API_KEY", "keen-test")
    client = _client()
    asyncio.run(_extractor().extract(URL, client))
    client.get.assert_awaited_once_with(
        KEENABLE_FETCH_URL,
        params={"url": URL},
        headers={"X-Keenable-Title": "Horizon", "X-API-Key": "keen-test"},
    )


def test_uses_configured_env_var(monkeypatch):
    monkeypatch.setenv("MY_KEENABLE_KEY", "keen-other")
    client = _client()
    asyncio.run(_extractor(api_key_env="MY_KEENABLE_KEY").extract(URL, client))
    args, kwargs = client.get.call_args
    assert args == (KEENABLE_FETCH_URL,)
    assert kwargs["headers"]["X-API-Key"] == "keen-other"


def test_blank_api_key_falls_back_to_keyless(monkeypatch):
    monkeypatch.setenv("KEENABLE_API_KEY", "  ")
    client = _client()
    asyncio.run(_extractor().extract(URL, client))
    args, kwargs = client.get.call_args
    assert args == (KEENABLE_PUBLIC_FETCH_URL,)
    assert "X-API-Key" not in kwargs["headers"]


def test_returns_none_on_http_error():
    client = _client(status=429)
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_on_timeout():
    client = AsyncMock()
    client.get.side_effect = httpx.ReadTimeout("timed out")
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_on_empty_content():
    client = _client({"url": URL, "content": ""})
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


@pytest.mark.parametrize("payload", [
    {"content": 123},
    {"content": ["not text"]},
    {"content": {"text": "not a string"}},
    {"content": "  \n\t"},
    {"content": None},
    {"url": URL},
    None,
    [],
], ids=[
    "number", "list", "object", "blank", "null-content", "missing-content",
    "null-response", "list-response",
])
def test_invalid_fetch_preserves_rss_article(payload):
    feed = """<rss version="2.0"><channel><title>Test</title><item>
      <guid>one</guid><title>Article</title><link>https://example.com/article</link>
      <pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate>
      <description>Useful feed text</description>
    </item></channel></rss>"""

    def handler(request):
        if request.url.host == "example.com":
            return httpx.Response(200, text=feed)
        assert str(request.url).startswith(KEENABLE_PUBLIC_FETCH_URL)
        return httpx.Response(200, text=json.dumps(payload), headers={"Content-Type": "application/json"})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            source = RSSSourceConfig(
                name="Test", url="https://example.com/feed.xml", content_extractor="keenable",
            )
            return await RSSScraper([source], client, extractors=ExtractorRegistry({})).fetch(
                datetime(2026, 10, 29, tzinfo=timezone.utc),
            )

    result = asyncio.run(run())
    assert result.status == "success"
    assert len(result.items) == 1
    assert result.items[0].content == "Useful feed text"
    assert result.failures == {}


def test_extracted_markdown_replaces_rss_content():
    feed = """<rss version="2.0"><channel><title>Test</title><item>
      <guid>one</guid><title>Article</title><link>https://example.com/article</link>
      <pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate>
      <description>Short feed text</description>
    </item></channel></rss>"""
    fetches = []

    def handler(request):
        if request.url.host == "example.com":
            return httpx.Response(200, text=feed)
        fetches.append(request)
        return httpx.Response(200, json={"url": URL, "content": "# Article\n\nFull text."})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            source = RSSSourceConfig(
                name="Test", url="https://example.com/feed.xml", content_extractor="keenable",
            )
            return await RSSScraper([source], client, extractors=ExtractorRegistry({})).fetch(
                datetime(2026, 10, 29, tzinfo=timezone.utc),
            )

    result = asyncio.run(run())
    assert result.items[0].content == "# Article\n\nFull text."
    (fetch,) = fetches
    assert fetch.url.params["url"] == URL
    assert fetch.headers["X-Keenable-Title"] == "Horizon"
