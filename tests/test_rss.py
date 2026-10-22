from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import feedparser
import httpx
import pytest

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
    response.raise_for_status.return_value = None
    client = AsyncMock()
    client.get.return_value = response
    return client


def test_rss_ids_are_deterministic() -> None:
    client = _make_feed_client(_FEED)
    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", profile="rss-profile"
    )
    scraper = RSSScraper([source], client)

    first_item = asyncio.run(scraper.fetch(_SINCE)).items[0]
    first = first_item.id
    second = asyncio.run(scraper.fetch(_SINCE)).items[0].id

    assert first == second
    assert first == "rss:example.com_feed.xml:5e2d5d1e58e94d76"
    assert first_item.profile == "rss-profile"


def test_timezone_less_pubdate_is_treated_as_utc() -> None:
    client = _make_feed_client(_FEED.replace(" GMT", ""))
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")
    scraper = RSSScraper([source], client)

    items = asyncio.run(scraper.fetch(_SINCE)).items

    assert len(items) == 1
    assert items[0].published_at == datetime(
        2026, 4, 24, 12, 0, tzinfo=timezone.utc
    )


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
    items = asyncio.run(scraper.fetch(_SINCE)).items

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
    items = asyncio.run(scraper.fetch(_SINCE)).items

    assert len(items) == 1
    assert items[0].content == "Short summary from feed."


def test_unknown_extractor_name_ignored() -> None:
    client = _make_feed_client(_FEED)
    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", content_extractor="nonexistent"
    )
    scraper = RSSScraper([source], client, extractors=_make_registry("other", AsyncMock()))
    items = asyncio.run(scraper.fetch(_SINCE)).items

    assert len(items) == 1
    assert items[0].content == "Short summary from feed."


_THREE_ENTRIES = _FEED.replace(
    "</channel>",
    """<item>
    <guid>entry-2</guid><title>Item 2</title>
    <link>https://example.com/item-2</link>
    <pubDate>Fri, 24 Apr 2026 12:00:00 GMT</pubDate>
  </item>
  <item>
    <guid>entry-3</guid><title>Item 3</title>
    <link>https://example.com/item-3</link>
    <pubDate>Fri, 24 Apr 2026 12:00:00 GMT</pubDate>
  </item>
</channel>""",
)


def test_invalid_entry_url_keeps_siblings_and_reports_warning(caplog) -> None:
    feed = _THREE_ENTRIES.replace("https://example.com/item-2", "mailto:invalid")
    client = _make_feed_client(feed)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    with caplog.at_level(logging.WARNING, logger="src.scrapers.rss"):
        result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert [item.title for item in result.items] == ["Item 1", "Item 3"]
    assert result.status == "partial_failure"
    assert result.successful == 1
    assert set(result.failures) == {"Test/entry:2"}
    assert result.failures["Test/entry:2"].startswith("ValidationError:")
    assert len(caplog.records) == 1
    warning = caplog.records[0].getMessage()
    assert "Test/entry:2" in warning
    assert "ValidationError" in warning
    assert "validation error" in warning
    assert "mailto:invalid" not in warning
    assert "input_value" not in warning


def test_invalid_entry_tags_keep_siblings(monkeypatch, caplog) -> None:
    parsed = feedparser.parse(_THREE_ENTRIES)
    parsed.entries[1]["tags"] = [object()]
    monkeypatch.setattr("src.scrapers.rss.feedparser.parse", lambda _: parsed)
    client = _make_feed_client(_THREE_ENTRIES)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    with caplog.at_level(logging.WARNING, logger="src.scrapers.rss"):
        result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert [item.title for item in result.items] == ["Item 1", "Item 3"]
    assert result.status == "partial_failure"
    assert set(result.failures) == {"Test/entry:2"}
    assert "AttributeError" in caplog.text
    assert "term" in caplog.text


def test_all_invalid_entries_report_each_failure() -> None:
    feed = _THREE_ENTRIES.replace("https://example.com/item-", "mailto:invalid-")
    client = _make_feed_client(feed)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert result.items == []
    assert result.status == "failure"
    assert result.successful == 0
    assert set(result.failures) == {
        "Test/entry:1", "Test/entry:2", "Test/entry:3"
    }


@pytest.mark.parametrize("feed", [
    '<rss version="2.0"><channel/></rss>',
    _FEED.replace("Fri, 24 Apr 2026 12:00:00 GMT", "not a date"),
    _FEED.replace("24 Apr", "23 Apr"),
], ids=["empty", "undated", "old"])
def test_empty_or_filtered_feed_is_successful(feed) -> None:
    client = _make_feed_client(feed)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert result.items == []
    assert result.status == "empty"
    assert result.successful == 1
    assert result.failures == {}


def test_http_error_remains_a_feed_failure() -> None:
    client = _make_feed_client(_FEED)
    client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service unavailable", request=httpx.Request("GET", "https://example.com/feed.xml"),
        response=httpx.Response(503),
    )
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert result.items == []
    assert result.status == "failure"
    assert result.successful == 0
    assert set(result.failures) == {"Test"}
    assert result.failures["Test"].startswith("HTTPStatusError:")


@pytest.mark.parametrize("parse_raises", [False, True], ids=["bozo", "exception"])
def test_parser_error_remains_a_feed_failure(monkeypatch, parse_raises) -> None:
    if parse_raises:
        def parse(_):
            raise ValueError("Parser failed")
        monkeypatch.setattr("src.scrapers.rss.feedparser.parse", parse)
    client = _make_feed_client("not an RSS feed")
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert result.items == []
    assert result.status == "failure"
    assert result.successful == 0
    assert set(result.failures) == {"Test"}
    assert result.failures["Test"].startswith("ValueError:")


def test_date_processing_error_is_isolated(monkeypatch) -> None:
    client = _make_feed_client(_THREE_ENTRIES)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")
    scraper = RSSScraper([source], client)
    parse_date = scraper._parse_date

    def parse(entry):
        if entry.title == "Item 2":
            raise TypeError("Unexpected date object")
        return parse_date(entry)

    monkeypatch.setattr(scraper, "_parse_date", parse)
    result = asyncio.run(scraper.fetch(_SINCE))

    assert [item.title for item in result.items] == ["Item 1", "Item 3"]
    assert result.status == "partial_failure"
    assert result.failures == {"Test/entry:2": "TypeError: Unexpected date object"}


def test_extractor_error_is_isolated_and_reason_is_concise(caplog) -> None:
    client = _make_feed_client(_THREE_ENTRIES)
    extractor = AsyncMock()
    extractor.extract.side_effect = ["First article", RuntimeError(
        "Extraction failed\nentry payload must not be logged"
    ), "Third article"]
    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", content_extractor="my-ext"
    )
    scraper = RSSScraper([source], client, extractors=_make_registry("my-ext", extractor))

    with caplog.at_level(logging.WARNING, logger="src.scrapers.rss"):
        result = asyncio.run(scraper.fetch(_SINCE))

    assert [item.content for item in result.items] == ["First article", "Third article"]
    assert result.status == "partial_failure"
    assert result.failures == {"Test/entry:2": "RuntimeError: Extraction failed"}
    assert "entry payload" not in caplog.text


def test_entry_cancellation_propagates() -> None:
    client = _make_feed_client(_FEED)
    extractor = AsyncMock()
    extractor.extract.side_effect = asyncio.CancelledError()
    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", content_extractor="my-ext"
    )
    scraper = RSSScraper([source], client, extractors=_make_registry("my-ext", extractor))

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(scraper.fetch(_SINCE))
