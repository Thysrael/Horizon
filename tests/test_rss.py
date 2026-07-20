from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from src.models import RSSSourceConfig
from src.scrapers.rss import RSSScraper

_FEED = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"><channel><title>Test</title>
  <item>
    <guid>entry-1</guid>
    <title>Item 1</title>
    <link>https://example.com/item-1</link>
    <pubDate>Fri, 24 Apr 2026 12:00:00 GMT</pubDate>
    <description>Short summary from feed.</description>
  </item>
</channel></rss>
"""
_SINCE = datetime(2026, 4, 24, 0, 0, tzinfo=timezone.utc)


def _make_feed_client(feed_text: str) -> AsyncMock:
    response = MagicMock()
    response.text = feed_text
    response.status_code = 200
    response.headers = {}
    response.raise_for_status.return_value = None
    client = AsyncMock()
    client.get.return_value = response
    return client


def test_rss_ids_are_deterministic() -> None:
    client = _make_feed_client(_FEED)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")
    scraper = RSSScraper([source], client)

    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34"}),
    ):
        first = asyncio.run(scraper.fetch(_SINCE))[0].id
        second = asyncio.run(scraper.fetch(_SINCE))[0].id

    assert first == second
    assert first == "rss:example.com_feed.xml:5e2d5d1e58e94d76"


def _make_registry(name: str, extractor):
    registry = MagicMock()
    registry.get.side_effect = lambda n: extractor if n == name else None
    return registry


def test_content_extractor_replaces_feed_content() -> None:
    client = _make_feed_client(_FEED)
    extractor = AsyncMock()
    extractor.extract.return_value = "Full article text from extractor."

    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", content_extractor="my-ext"
    )
    scraper = RSSScraper([source], client, extractors=_make_registry("my-ext", extractor))
    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34"}),
    ):
        items = asyncio.run(scraper.fetch(_SINCE))

    assert len(items) == 1
    assert items[0].content == "Full article text from extractor."
    extractor.extract.assert_awaited_once_with("https://example.com/item-1", client)


def test_content_extractor_falls_back_on_none() -> None:
    client = _make_feed_client(_FEED)
    extractor = AsyncMock()
    extractor.extract.return_value = None  # extraction failed

    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", content_extractor="my-ext"
    )
    scraper = RSSScraper([source], client, extractors=_make_registry("my-ext", extractor))
    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34"}),
    ):
        items = asyncio.run(scraper.fetch(_SINCE))

    assert len(items) == 1
    assert items[0].content == "Short summary from feed."


def test_unknown_extractor_name_ignored() -> None:
    client = _make_feed_client(_FEED)
    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", content_extractor="nonexistent"
    )
    scraper = RSSScraper([source], client, extractors=_make_registry("other", AsyncMock()))
    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34"}),
    ):
        items = asyncio.run(scraper.fetch(_SINCE))

    assert len(items) == 1
    assert items[0].content == "Short summary from feed."


def test_rss_fetches_public_feed_through_validated_request_path() -> None:
    client = _make_feed_client(_FEED)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")
    scraper = RSSScraper([source], client)

    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34"}),
    ):
        items = asyncio.run(scraper.fetch(_SINCE))

    assert len(items) == 1
    client.get.assert_awaited_once_with(
        "https://example.com/feed.xml", follow_redirects=False
    )


def test_rss_refuses_private_dns_result_before_parsing_content() -> None:
    client = _make_feed_client(_FEED)
    source = RSSSourceConfig(name="Internal", url="https://feed.example/feed.xml")
    scraper = RSSScraper([source], client)

    with (
        patch(
            "src.url_security._resolve_hostname",
            new=AsyncMock(return_value={"10.0.0.2"}),
        ),
        patch("src.scrapers.rss.feedparser.parse") as parse,
    ):
        items = asyncio.run(scraper.fetch(_SINCE))

    assert items == []
    client.get.assert_not_awaited()
    parse.assert_not_called()


def test_rss_refuses_redirect_to_private_address_before_parsing_content() -> None:
    redirect = MagicMock(
        status_code=302,
        headers={"location": "http://127.0.0.1/internal-feed"},
    )
    client = AsyncMock()
    client.get.return_value = redirect
    source = RSSSourceConfig(name="Redirect", url="https://feed.example/feed.xml")
    scraper = RSSScraper([source], client)

    with (
        patch(
            "src.url_security._resolve_hostname",
            new=AsyncMock(side_effect=[{"93.184.216.34"}, {"127.0.0.1"}]),
        ),
        patch("src.scrapers.rss.feedparser.parse") as parse,
    ):
        items = asyncio.run(scraper.fetch(_SINCE))

    assert items == []
    client.get.assert_awaited_once_with(
        "https://feed.example/feed.xml", follow_redirects=False
    )
    parse.assert_not_called()
