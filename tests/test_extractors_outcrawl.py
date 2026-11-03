from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.extractors import ExtractorRegistry, OutcrawlExtractor
from src.extractors.outcrawl import OUTCRAWL_SCRAPE_URL
from src.models import OutcrawlExtractorConfig, RSSSourceConfig
from src.scrapers.rss import RSSScraper

URL = "https://example.com/article"


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("OUTCRAWL_API_KEY", "oc-test")


def _extractor(**kwargs) -> OutcrawlExtractor:
    return OutcrawlExtractor(OutcrawlExtractorConfig(**kwargs))


def _client(payload=None, status: int = 200) -> AsyncMock:
    response = MagicMock()
    response.json.return_value = payload if payload is not None else {
        "url": URL,
        "statusCode": 200,
        "markdown": "# Title\n\nArticle text.",
        "metadata": {"title": "Title"},
    }
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
        OUTCRAWL_SCRAPE_URL,
        headers={"Authorization": "Bearer oc-test"},
        json={
            "url": URL,
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
        timeout=65.0,
    )


def test_uses_configured_env_var_and_options(monkeypatch):
    monkeypatch.setenv("MY_OUTCRAWL_KEY", "oc-other")
    client = _client()
    asyncio.run(_extractor(api_key_env="MY_OUTCRAWL_KEY", only_main_content=False).extract(URL, client))
    _, kwargs = client.post.call_args
    assert kwargs["headers"] == {"Authorization": "Bearer oc-other"}
    assert kwargs["json"]["onlyMainContent"] is False


def test_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("OUTCRAWL_API_KEY")
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


def test_returns_none_on_empty_markdown():
    client = _client({"url": URL, "markdown": ""})
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


@pytest.mark.parametrize("payload", [
    {"markdown": 123},
    {"markdown": ["not text"]},
    {"markdown": {"text": "not a string"}},
    {"markdown": "  \n\t"},
    {"markdown": None},
    {"url": URL},
    None,
    [],
], ids=[
    "number", "list", "object", "blank", "null-markdown", "missing-markdown",
    "null-response", "list-response",
])
def test_invalid_scrape_preserves_rss_article(payload):
    feed = """<rss version="2.0"><channel><title>Test</title><item>
      <guid>one</guid><title>Article</title><link>https://example.com/article</link>
      <pubDate>Thu, 29 Oct 2026 12:00:00 GMT</pubDate>
      <description>Useful feed text</description>
    </item></channel></rss>"""

    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, text=feed)
        assert str(request.url) == OUTCRAWL_SCRAPE_URL
        return httpx.Response(200, text=json.dumps(payload), headers={"Content-Type": "application/json"})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            source = RSSSourceConfig(
                name="Test", url="https://example.com/feed.xml", content_extractor="outcrawl",
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
        return httpx.Response(200, json={"url": URL, "markdown": "# Article\n\nFull text."})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            source = RSSSourceConfig(
                name="Test", url="https://example.com/feed.xml", content_extractor="outcrawl",
            )
            return await RSSScraper([source], client, extractors=ExtractorRegistry({})).fetch(
                datetime(2026, 10, 29, tzinfo=timezone.utc),
            )

    result = asyncio.run(run())
    assert result.items[0].content == "# Article\n\nFull text."


def test_scrape_timeout_override_does_not_change_shared_client():
    requests = []
    markdown = "  # Article\n\nFull text.\n"

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"url": URL, "markdown": markdown})

    async def run():
        async with httpx.AsyncClient(timeout=30, transport=httpx.MockTransport(handler)) as client:
            assert await _extractor().extract(URL, client) == markdown
            await client.get(URL)

    asyncio.run(run())
    scrape, other = requests
    assert scrape.extensions["timeout"]["read"] == 65
    assert other.extensions["timeout"]["read"] == 30
