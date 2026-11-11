from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.extractors import ExtractorRegistry, SpecStreamExtractor
from src.extractors.specstream import SPECSTREAM_EXTRACT_URL
from src.models import RSSSourceConfig, SpecStreamExtractorConfig
from src.scrapers.rss import RSSScraper

URL = "https://example.com/article"


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("SPECSTREAM_API_KEY", "ss-test")


def _extractor(**kwargs) -> SpecStreamExtractor:
    return SpecStreamExtractor(SpecStreamExtractorConfig(**kwargs))


def _page(**fields) -> dict:
    page = {
        "url": URL,
        "status": "ok",
        "title": "Title",
        "text": "# Title\n\nArticle text.",
        "published": "2026-10-29",
    }
    page.update(fields)
    return {"data": {"request_id": "req_1", "results": [page], "took_ms": 900, "price_usd": 0.0008}}


def _client(payload=None, status: int = 200) -> AsyncMock:
    response = MagicMock()
    response.json.return_value = payload if payload is not None else _page()
    response.raise_for_status.return_value = None
    if status >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=str(status), request=MagicMock(), response=MagicMock()
        )
    client = AsyncMock()
    client.post.return_value = response
    return client


def test_returns_markdown():
    client = _client()
    result = asyncio.run(_extractor().extract(URL, client))
    assert result == "# Title\n\nArticle text."
    client.post.assert_awaited_once_with(
        SPECSTREAM_EXTRACT_URL,
        headers={"Authorization": "Bearer ss-test"},
        json={"urls": [URL], "format": "markdown"},
        timeout=35.0,
    )


def test_uses_configured_env_var(monkeypatch):
    monkeypatch.setenv("MY_SPECSTREAM_KEY", "ss-other")
    client = _client()
    asyncio.run(_extractor(api_key_env="MY_SPECSTREAM_KEY").extract(URL, client))
    _, kwargs = client.post.call_args
    assert kwargs["headers"] == {"Authorization": "Bearer ss-other"}


def test_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("SPECSTREAM_API_KEY")
    client = _client()
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None
    client.post.assert_not_awaited()


def test_returns_none_on_http_error():
    client = _client(status=402)
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_on_timeout():
    client = AsyncMock()
    client.post.side_effect = httpx.ReadTimeout("timed out")
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


@pytest.mark.parametrize("status", ["blocked", "not_found", "empty", "unsupported", "failed"])
def test_returns_none_when_page_not_read(status):
    client = _client(_page(status=status, text=""))
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


@pytest.mark.parametrize("payload", [
    _page(text=123),
    _page(text="  \n\t"),
    _page(text=None),
    {"data": {"results": []}},
    {"data": {}},
    {"error": {"code": "invalid_token", "message": "Unknown key"}},
    None,
    [],
], ids=[
    "number", "blank", "null-text", "no-results", "missing-results", "error-envelope",
    "null-response", "list-response",
])
def test_invalid_extract_preserves_rss_article(payload):
    feed = """<rss version="2.0"><channel><title>Test</title><item>
      <guid>one</guid><title>Article</title><link>https://example.com/article</link>
      <pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate>
      <description>Useful feed text</description>
    </item></channel></rss>"""

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, text=feed)
        assert str(request.url) == SPECSTREAM_EXTRACT_URL
        return httpx.Response(200, text=json.dumps(payload), headers={"Content-Type": "application/json"})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            source = RSSSourceConfig(
                name="Test", url="https://example.com/feed.xml", content_extractor="specstream",
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

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, text=feed)
        return httpx.Response(200, json=_page(text="# Article\n\nFull text."))

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            source = RSSSourceConfig(
                name="Test", url="https://example.com/feed.xml", content_extractor="specstream",
            )
            return await RSSScraper([source], client, extractors=ExtractorRegistry({})).fetch(
                datetime(2026, 10, 29, tzinfo=timezone.utc),
            )

    result = asyncio.run(run())
    assert result.items[0].content == "# Article\n\nFull text."


def test_extract_timeout_override_does_not_change_shared_client():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=_page())

    async def run():
        async with httpx.AsyncClient(timeout=30, transport=httpx.MockTransport(handler)) as client:
            assert await _extractor().extract(URL, client) == "# Title\n\nArticle text."
            await client.get(URL)

    asyncio.run(run())
    extract, other = requests
    assert json.loads(extract.content) == {"urls": [URL], "format": "markdown"}
    assert extract.extensions["timeout"]["read"] == 35
    assert other.extensions["timeout"]["read"] == 30
