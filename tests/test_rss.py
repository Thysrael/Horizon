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


_FULL_CONTENT = "<p>The full article contains more detail than the short summary.</p>"
_FULL_RSS_FEED = _FEED.replace(
    '<rss version="2.0">',
    '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">',
).replace(
    "</item>", f"<content:encoded><![CDATA[{_FULL_CONTENT}]]></content:encoded></item>"
)
_FULL_ATOM_FEED = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test</title><id>https://example.com/</id>
  <updated>2026-04-24T12:00:00Z</updated>
  <entry>
    <id>entry-1</id><title>Item 1</title>
    <link href="https://example.com/item-1"/>
    <updated>2026-04-24T12:00:00Z</updated>
    <summary>Short summary from feed.</summary>
    <content type="html"><![CDATA[{_FULL_CONTENT}]]></content>
  </entry>
</feed>
"""


@pytest.mark.parametrize("feed", [_FULL_RSS_FEED, _FULL_ATOM_FEED], ids=["rss", "atom"])
def test_full_feed_content_is_not_hidden_by_summary(feed) -> None:
    client = _make_feed_client(feed)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert result.status == "success"
    assert len(result.items) == 1
    assert result.items[0].content == _FULL_CONTENT


def test_atom_parameterized_xhtml_content_is_not_hidden_by_summary() -> None:
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test</title><id>https://example.com/</id>
  <updated>2026-04-24T12:00:00Z</updated>
  <author><name>Example</name></author>
  <entry>
    <id>https://example.com/item-1</id><title>Item 1</title>
    <link href="https://example.com/item-1"/>
    <updated>2026-04-24T12:00:00Z</updated>
    <summary>Short summary from feed.</summary>
    <content type="application/xhtml+xml; charset=utf-8"><![CDATA[{_FULL_CONTENT}]]></content>
  </entry>
</feed>
"""
    parsed = feedparser.parse(feed)
    assert not parsed.bozo
    assert parsed.entries[0].content[0].type == "application/xhtml+xml; charset=utf-8"
    assert parsed.entries[0].content[0].value == _FULL_CONTENT
    client = _make_feed_client(feed)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert result.status == "success"
    assert len(result.items) == 1
    assert result.items[0].content == _FULL_CONTENT


def test_atom_inline_png_content_does_not_hide_summary() -> None:
    png = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
        "+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test</title><id>https://example.com/</id>
  <updated>2026-04-24T12:00:00Z</updated>
  <author><name>Example</name></author>
  <entry>
    <id>https://example.com/item-1</id><title>Item 1</title>
    <link href="https://example.com/item-1"/>
    <updated>2026-04-24T12:00:00Z</updated>
    <summary>Readable summary.</summary>
    <content type="image/png">{png}</content>
  </entry>
</feed>
"""
    parsed = feedparser.parse(feed)
    assert not parsed.bozo
    assert parsed.entries[0].content[0].type == "image/png"
    assert parsed.entries[0].content[0].value == png
    client = _make_feed_client(feed)
    source = RSSSourceConfig(name="Test", url="https://example.com/feed.xml")

    result = asyncio.run(RSSScraper([source], client).fetch(_SINCE))

    assert result.status == "success"
    assert len(result.items) == 1
    assert result.items[0].content == "Readable summary."


@pytest.mark.parametrize("fields,expected", [
    ({"content": [{"value": "whole"}], "summary": "tease"}, "whole"),
    ({"content": [{"value": "short"}], "summary": "A longer summary"}, "A longer summary"),
    ({"content": [{"value": "tiny"}, {"value": "The longest alternative"}],
      "summary": "A summary"}, "The longest alternative"),
    ({"content": [{"value": "first"}, {"value": "later"}]}, "first"),
    ({"content": [{"value": "Article"}], "summary": "  \n"}, "Article"),
    ({"content": [{"value": "Article"}], "summary": None}, "Article"),
    ({"content": [None, "not a mapping", {"value": 42}, {"value": "Full article"}],
      "summary": "Teaser"}, "Full article"),
    ({"content": [{"value": 42}], "summary": "Text summary"}, "Text summary"),
    ({"content": [{"value": "  \n"}], "summary": ""}, ""),
    ({}, ""),
    ({"description": "Description only"}, "Description only"),
    ({"content": [{}]}, ""),
    ({"content": 42, "summary": "Fallback summary"}, "Fallback summary"),
    ({"content": [{"value": "  <p>" + "article " * 3000 + "</p>\n"}],
      "summary": "Teaser"}, "  <p>" + "article " * 3000 + "</p>\n"),
], ids=[
    "content_wins_tie", "longer_summary", "later_content", "first_content_wins_tie",
    "blank_summary", "nonstring_summary", "malformed_alternatives", "nonstring_values",
    "blank_candidates", "missing_candidates", "description_only", "missing_value",
    "malformed_content_container", "preserve_representation",
])
def test_content_selection_candidates(fields, expected) -> None:
    scraper = RSSScraper([], _make_feed_client(_FEED))

    assert scraper._extract_content(feedparser.FeedParserDict(fields)) == expected


@pytest.mark.parametrize("media_type,is_text", [
    ("", True),
    ("text/plain", True),
    ("text/html", True),
    ("text/markdown", True),
    ("html", True),
    ("xhtml", True),
    ("application/xhtml+xml", True),
    ("application/xhtml+xml; charset=utf-8", True),
    (" APPLICATION/XHTML+XML ; charset=UTF-8 ", True),
    ("text/plain; charset=utf-8", True),
    ("image/png", False),
    ("audio/mpeg", False),
    ("application/octet-stream", False),
    ("application/xml", False),
    (None, False),
    (42, False),
])
def test_content_selection_respects_media_type(media_type, is_text) -> None:
    scraper = RSSScraper([], _make_feed_client(_FEED))
    entry = feedparser.FeedParserDict({
        "content": [{"type": media_type, "value": "Full article"}],
        "summary": "Summary",
    })

    assert scraper._extract_content(entry) == ("Full article" if is_text else "Summary")


@pytest.mark.parametrize("extracted", ["Extractor text", None], ids=["override", "fallback"])
def test_extractor_still_overrides_longest_feed_content(extracted) -> None:
    client = _make_feed_client(_FULL_RSS_FEED)
    extractor = AsyncMock()
    extractor.extract.return_value = extracted
    source = RSSSourceConfig(
        name="Test", url="https://example.com/feed.xml", content_extractor="my-ext"
    )
    scraper = RSSScraper([source], client, extractors=_make_registry("my-ext", extractor))

    result = asyncio.run(scraper.fetch(_SINCE))

    assert result.status == "success"
    assert result.items[0].content == (extracted if extracted is not None else _FULL_CONTENT)
    extractor.extract.assert_awaited_once_with("https://example.com/item-1", client)
