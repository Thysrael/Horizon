from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import httpx

from src.models import GoogleNewsConfig
from src.scrapers.google_news import GoogleNewsScraper


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _feed(items_xml: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
      <title>Google News</title>
      {items_xml}
    </channel></rss>
    """


def _item(
    title: str,
    link: str,
    pub: str = "Sat, 27 Jun 2026 12:00:00 GMT",
    source: str | None = "Publisher",
) -> str:
    source_tag = f"<source>{source}</source>" if source is not None else ""
    return f"""
      <item>
        <title>{title}</title>
        <link>{link}</link>
        <guid>{link}</guid>
        <pubDate>{pub}</pubDate>
        <description>Summary text</description>
        {source_tag}
      </item>
    """


def _mock_client(text: str) -> AsyncMock:
    response = MagicMock()
    response.text = text
    response.raise_for_status.return_value = None
    client = AsyncMock()
    client.get.return_value = response
    return client


def test_short_window_uses_when_operator() -> None:
    client = _mock_client(_feed(_item("Foo - Publisher", "https://example.com/a")))
    config = GoogleNewsConfig(enabled=True, query="ai")
    scraper = GoogleNewsScraper(config, client)

    since = _now() - timedelta(hours=24)
    asyncio.run(scraper.fetch(since))

    q = client.get.call_args.kwargs["params"]["q"]
    assert "when:" in q
    assert q.endswith("h")
    assert q.startswith("ai ")


def test_long_window_uses_after_operator() -> None:
    client = _mock_client(_feed(_item("Foo - Publisher", "https://example.com/a")))
    config = GoogleNewsConfig(enabled=True, query="ai")
    scraper = GoogleNewsScraper(config, client)

    since = _now() - timedelta(days=30)
    asyncio.run(scraper.fetch(since))

    q = client.get.call_args.kwargs["params"]["q"]
    assert "after:" in q
    assert "when:" not in q


def test_ceid_defaults_when_unset() -> None:
    client = _mock_client(_feed(_item("Foo - Publisher", "https://example.com/a")))
    config = GoogleNewsConfig(enabled=True, query="ai", language="en", country="US")
    scraper = GoogleNewsScraper(config, client)

    asyncio.run(scraper.fetch(_now() - timedelta(hours=6)))

    params = client.get.call_args.kwargs["params"]
    assert params["ceid"] == "US:en"
    assert params["hl"] == "en"
    assert params["gl"] == "US"


def test_parses_feed_into_content_items() -> None:
    items_xml = _item(
        "Headline One - Publisher",
        "https://example.com/a",
        pub="Sat, 27 Jun 2026 12:00:00 GMT",
    ) + _item(
        "Headline Two - Other",
        "https://example.com/b",
        pub="Sat, 27 Jun 2026 13:00:00 GMT",
        source="Other",
    )
    client = _mock_client(_feed(items_xml))
    config = GoogleNewsConfig(enabled=True, query="ai")
    scraper = GoogleNewsScraper(config, client)

    items = asyncio.run(scraper.fetch(_now() - timedelta(days=365)))

    assert len(items) == 2
    first = items[0]
    assert first.title == "Headline One - Publisher"
    assert str(first.url) == "https://example.com/a"
    assert first.published_at == datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
    assert first.id.startswith("google_news:article:")
    assert first.metadata["gn_query"] == "ai"
    assert first.metadata["source_name"] == "Publisher"


def test_disabled_config_returns_empty() -> None:
    client = _mock_client(_feed(_item("Foo", "https://example.com/a")))
    config = GoogleNewsConfig(enabled=False, query="ai")
    scraper = GoogleNewsScraper(config, client)

    assert asyncio.run(scraper.fetch(_now())) == []


def test_empty_query_returns_empty() -> None:
    client = _mock_client(_feed(_item("Foo", "https://example.com/a")))
    config = GoogleNewsConfig(enabled=True, query="   ")
    scraper = GoogleNewsScraper(config, client)

    assert asyncio.run(scraper.fetch(_now())) == []


def test_http_error_returns_empty() -> None:
    client = AsyncMock()
    client.get.side_effect = httpx.HTTPError("boom")
    config = GoogleNewsConfig(enabled=True, query="ai")
    scraper = GoogleNewsScraper(config, client)

    assert asyncio.run(scraper.fetch(_now())) == []


def test_empty_feed_returns_empty() -> None:
    client = _mock_client(_feed(""))
    config = GoogleNewsConfig(enabled=True, query="ai")
    scraper = GoogleNewsScraper(config, client)

    assert asyncio.run(scraper.fetch(_now())) == []


def test_entry_missing_link_or_title_is_skipped() -> None:
    items_xml = (
        _item("", "https://example.com/no-title")  # missing title
        + "<item><title>No link</title><pubDate>Sat, 27 Jun 2026 12:00:00 GMT</pubDate></item>"
        + _item("Good - Publisher", "https://example.com/good")
    )
    client = _mock_client(_feed(items_xml))
    config = GoogleNewsConfig(enabled=True, query="ai")
    scraper = GoogleNewsScraper(config, client)

    items = asyncio.run(scraper.fetch(_now() - timedelta(days=365)))

    assert len(items) == 1
    assert str(items[0].url) == "https://example.com/good"


def test_max_results_cap() -> None:
    items_xml = "".join(
        _item(f"Item {i} - Pub", f"https://example.com/{i}") for i in range(5)
    )
    client = _mock_client(_feed(items_xml))
    config = GoogleNewsConfig(enabled=True, query="ai", max_results=2)
    scraper = GoogleNewsScraper(config, client)

    items = asyncio.run(scraper.fetch(_now() - timedelta(days=365)))

    assert len(items) == 2
