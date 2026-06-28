from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import httpx

from src.models import GDELTConfig
from src.scrapers.gdelt import GDELTScraper


SINCE = datetime(2026, 6, 27, 8, 30, 0, tzinfo=timezone.utc)


def _mock_client(payload: dict | None = None) -> AsyncMock:
    response = MagicMock()
    response.json.return_value = payload if payload is not None else {}
    response.raise_for_status.return_value = None
    client = AsyncMock()
    client.get.return_value = response
    return client


def _articles_payload() -> dict:
    return {
        "articles": [
            {
                "url": "https://example.com/ai-1",
                "title": "AI breakthrough one",
                "seendate": "20260628T120000Z",
                "domain": "example.com",
                "sourcecountry": "United States",
                "language": "English",
                "socialimage": "https://example.com/img1.jpg",
            },
            {
                "url": "https://news.test/ai-2",
                "title": "AI breakthrough two",
                "seendate": "20260628T130000Z",
                "domain": "news.test",
                "sourcecountry": "United Kingdom",
                "language": "English",
            },
        ]
    }


def test_time_window_uses_startdatetime_when_no_timespan() -> None:
    client = _mock_client(_articles_payload())
    config = GDELTConfig(enabled=True, query="ai")
    scraper = GDELTScraper(config, client)

    asyncio.run(scraper.fetch(SINCE))

    params = client.get.call_args.kwargs["params"]
    assert params["startdatetime"] == SINCE.strftime("%Y%m%d%H%M%S")
    assert "enddatetime" in params
    assert "timespan" not in params


def test_time_window_uses_timespan_when_set() -> None:
    client = _mock_client(_articles_payload())
    config = GDELTConfig(enabled=True, query="ai", timespan="24h")
    scraper = GDELTScraper(config, client)

    asyncio.run(scraper.fetch(SINCE))

    params = client.get.call_args.kwargs["params"]
    assert params["timespan"] == "24h"
    assert "startdatetime" not in params
    assert "enddatetime" not in params


def test_language_and_country_appended_to_query() -> None:
    client = _mock_client(_articles_payload())
    config = GDELTConfig(
        enabled=True, query="ai", language="english", country="US"
    )
    scraper = GDELTScraper(config, client)

    asyncio.run(scraper.fetch(SINCE))

    params = client.get.call_args.kwargs["params"]
    assert params["query"] == "ai sourcelang:english sourcecountry:US"


def test_parses_articles_into_content_items() -> None:
    client = _mock_client(_articles_payload())
    config = GDELTConfig(enabled=True, query="ai")
    scraper = GDELTScraper(config, client)

    items = asyncio.run(scraper.fetch(SINCE))

    assert len(items) == 2
    first = items[0]
    assert str(first.url) == "https://example.com/ai-1"
    assert first.title == "AI breakthrough one"
    assert first.published_at == datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    assert first.metadata["domain"] == "example.com"
    assert first.metadata["sourcecountry"] == "United States"
    assert first.id.startswith("gdelt:article:")


def test_disabled_config_returns_empty() -> None:
    client = _mock_client(_articles_payload())
    config = GDELTConfig(enabled=False, query="ai")
    scraper = GDELTScraper(config, client)

    assert asyncio.run(scraper.fetch(SINCE)) == []


def test_http_error_returns_empty() -> None:
    client = AsyncMock()
    client.get.side_effect = httpx.HTTPError("boom")
    config = GDELTConfig(enabled=True, query="ai")
    scraper = GDELTScraper(config, client)

    assert asyncio.run(scraper.fetch(SINCE)) == []


def test_missing_articles_key_returns_empty() -> None:
    client = _mock_client({"foo": "bar"})
    config = GDELTConfig(enabled=True, query="ai")
    scraper = GDELTScraper(config, client)

    assert asyncio.run(scraper.fetch(SINCE)) == []


def test_empty_query_returns_empty() -> None:
    client = _mock_client(_articles_payload())
    config = GDELTConfig(enabled=True, query="   ")
    scraper = GDELTScraper(config, client)

    assert asyncio.run(scraper.fetch(SINCE)) == []


def test_bad_article_is_skipped_not_crashing() -> None:
    payload = {
        "articles": [
            {  # missing url -> skipped
                "title": "No URL",
                "seendate": "20260628T120000Z",
                "domain": "example.com",
            },
            {  # unparseable seendate -> skipped
                "url": "https://example.com/bad-date",
                "title": "Bad date",
                "seendate": "not-a-date",
                "domain": "example.com",
            },
            {  # valid -> kept
                "url": "https://example.com/good",
                "title": "Good one",
                "seendate": "20260628T140000Z",
                "domain": "example.com",
            },
        ]
    }
    client = _mock_client(payload)
    config = GDELTConfig(enabled=True, query="ai")
    scraper = GDELTScraper(config, client)

    items = asyncio.run(scraper.fetch(SINCE))

    assert len(items) == 1
    assert str(items[0].url) == "https://example.com/good"


def test_non_json_body_returns_empty() -> None:
    response = MagicMock()
    response.json.side_effect = ValueError("no json")
    response.raise_for_status.return_value = None
    client = AsyncMock()
    client.get.return_value = response
    config = GDELTConfig(enabled=True, query="ai")
    scraper = GDELTScraper(config, client)

    assert asyncio.run(scraper.fetch(SINCE)) == []
