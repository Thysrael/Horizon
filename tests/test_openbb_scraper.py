"""Tests for the OpenBB scraper.

The tests do not require the ``openbb`` package to be installed. We
verify that:

* The scraper short-circuits to [] when the SDK is missing or disabled.
* It correctly maps OpenBB news records into ContentItems.
* It filters out items older than ``since`` and drops duplicates across
  watchlists by URL.
* Malformed OpenBB rows (missing url/date/title) are skipped instead of
  crashing the run.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest

from src.models import OpenBBConfig, OpenBBWatchlist, SourceType
from src.scrapers.openbb import OpenBBScraper


def _cfg(**overrides) -> OpenBBConfig:
    base = {
        "enabled": True,
        "watchlists": [
            OpenBBWatchlist(
                name="megacaps",
                symbols=["AAPL", "NVDA"],
                provider="yfinance",
                fetch_limit=5,
            )
        ],
    }
    base.update(overrides)
    return OpenBBConfig(**base)


def _make_scraper(config: OpenBBConfig, obb: object) -> OpenBBScraper:
    client = httpx.AsyncClient()
    scraper = OpenBBScraper(config, client)
    scraper._obb = obb
    return scraper


_SENTINEL = object()


def _news_row(
    *,
    title: str = "NVDA earnings beat",
    url: str = "https://example.com/nvda-earnings",
    date: object = _SENTINEL,
    author: str | None = "Reporter",
    body: str | None = "Body",
    symbols: object = "NVDA",
) -> SimpleNamespace:
    if date is _SENTINEL:
        date = datetime.now(timezone.utc)
    return SimpleNamespace(
        title=title,
        url=url,
        date=date,
        author=author,
        body=body,
        excerpt=None,
        symbols=symbols,
    )


class TestFetchGuards:
    def test_returns_empty_when_obb_not_installed(self):
        scraper = _make_scraper(_cfg(), obb=None)
        since = datetime.now(timezone.utc) - timedelta(days=1)
        result = asyncio.run(scraper.fetch(since))
        assert result == []

    def test_returns_empty_when_disabled(self):
        obb = MagicMock()
        scraper = _make_scraper(_cfg(enabled=False), obb=obb)
        since = datetime.now(timezone.utc) - timedelta(days=1)
        assert asyncio.run(scraper.fetch(since)) == []
        obb.news.company.assert_not_called()

    def test_skips_disabled_watchlist(self):
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(results=[])
        cfg = OpenBBConfig(
            enabled=True,
            watchlists=[
                OpenBBWatchlist(name="off", symbols=["AAPL"], enabled=False),
            ],
        )
        scraper = _make_scraper(cfg, obb=obb)
        since = datetime.now(timezone.utc) - timedelta(days=1)
        assert asyncio.run(scraper.fetch(since)) == []
        obb.news.company.assert_not_called()

    def test_skips_watchlist_with_no_symbols(self):
        obb = MagicMock()
        cfg = OpenBBConfig(
            enabled=True,
            watchlists=[OpenBBWatchlist(name="empty", symbols=[])],
        )
        scraper = _make_scraper(cfg, obb=obb)
        since = datetime.now(timezone.utc) - timedelta(days=1)
        assert asyncio.run(scraper.fetch(since)) == []
        obb.news.company.assert_not_called()


class TestMapping:
    def test_maps_single_news_row_into_content_item(self):
        now = datetime.now(timezone.utc)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[_news_row(date=now, symbols="NVDA,AAPL")]
        )
        scraper = _make_scraper(_cfg(), obb=obb)
        since = now - timedelta(hours=1)

        result = asyncio.run(scraper.fetch(since))

        assert len(result) == 1
        item = result[0]
        assert item.source_type == SourceType.OPENBB
        assert item.title == "NVDA earnings beat"
        assert item.content == "Body"
        assert item.metadata["watchlist"] == "megacaps"
        assert item.metadata["provider"] == "yfinance"
        assert item.metadata["symbols"] == ["NVDA", "AAPL"]
        assert item.id.startswith("openbb:news:")

    def test_passes_comma_joined_symbols_to_openbb(self):
        now = datetime.now(timezone.utc)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(results=[])
        scraper = _make_scraper(_cfg(), obb=obb)

        asyncio.run(scraper.fetch(now - timedelta(hours=1)))

        call_kwargs = obb.news.company.call_args.kwargs
        assert call_kwargs["symbol"] == "AAPL,NVDA"
        assert call_kwargs["provider"] == "yfinance"
        assert call_kwargs["limit"] == 5

    def test_falls_back_to_watchlist_symbols_when_row_has_none(self):
        now = datetime.now(timezone.utc)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[_news_row(date=now, symbols="")]
        )
        scraper = _make_scraper(_cfg(), obb=obb)
        result = asyncio.run(scraper.fetch(now - timedelta(hours=1)))
        assert result[0].metadata["symbols"] == ["AAPL", "NVDA"]

    def test_parses_iso_string_date(self):
        now = datetime.now(timezone.utc)
        iso = now.isoformat().replace("+00:00", "Z")
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[_news_row(date=iso)]
        )
        scraper = _make_scraper(_cfg(), obb=obb)
        result = asyncio.run(scraper.fetch(now - timedelta(hours=1)))
        assert len(result) == 1
        assert result[0].published_at.tzinfo is not None


class TestFiltering:
    def test_drops_items_older_than_since(self):
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=3)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[_news_row(date=old)]
        )
        scraper = _make_scraper(_cfg(), obb=obb)
        result = asyncio.run(scraper.fetch(now - timedelta(hours=1)))
        assert result == []

    def test_deduplicates_across_watchlists_by_url(self):
        now = datetime.now(timezone.utc)
        shared_url = "https://finance.yahoo.com/articles/abc"
        cfg = OpenBBConfig(
            enabled=True,
            watchlists=[
                OpenBBWatchlist(name="wl1", symbols=["AAPL"]),
                OpenBBWatchlist(name="wl2", symbols=["MSFT"]),
            ],
        )
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[_news_row(url=shared_url, date=now)]
        )
        scraper = _make_scraper(cfg, obb=obb)
        result = asyncio.run(scraper.fetch(now - timedelta(hours=1)))
        assert len(result) == 1
        assert result[0].metadata["watchlist"] == "wl1"
        assert obb.news.company.call_count == 2

    def test_handles_empty_results(self):
        now = datetime.now(timezone.utc)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(results=[])
        scraper = _make_scraper(_cfg(), obb=obb)
        assert asyncio.run(scraper.fetch(now - timedelta(hours=1))) == []


class TestResilience:
    def test_malformed_row_missing_url_is_skipped(self):
        now = datetime.now(timezone.utc)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[
                _news_row(url="", date=now),
                _news_row(date=now),
            ]
        )
        scraper = _make_scraper(_cfg(), obb=obb)
        result = asyncio.run(scraper.fetch(now - timedelta(hours=1)))
        assert len(result) == 1

    def test_malformed_row_missing_title_is_skipped(self):
        now = datetime.now(timezone.utc)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[_news_row(title="", date=now)]
        )
        scraper = _make_scraper(_cfg(), obb=obb)
        assert asyncio.run(scraper.fetch(now - timedelta(hours=1))) == []

    def test_malformed_row_missing_date_is_skipped(self):
        now = datetime.now(timezone.utc)
        obb = MagicMock()
        obb.news.company.return_value = SimpleNamespace(
            results=[_news_row(date=None)]
        )
        scraper = _make_scraper(_cfg(), obb=obb)
        assert asyncio.run(scraper.fetch(now - timedelta(hours=1))) == []

    def test_watchlist_exception_does_not_block_others(self):
        now = datetime.now(timezone.utc)
        cfg = OpenBBConfig(
            enabled=True,
            watchlists=[
                OpenBBWatchlist(name="boom", symbols=["AAPL"]),
                OpenBBWatchlist(name="ok", symbols=["MSFT"]),
            ],
        )
        obb = MagicMock()
        obb.news.company.side_effect = [
            RuntimeError("upstream 500"),
            SimpleNamespace(results=[_news_row(date=now)]),
        ]
        scraper = _make_scraper(cfg, obb=obb)
        result = asyncio.run(scraper.fetch(now - timedelta(hours=1)))
        assert len(result) == 1
        assert result[0].metadata["watchlist"] == "ok"


class TestStatic:
    @pytest.mark.parametrize("value,expected", [
        ("AAPL,MSFT", ["AAPL", "MSFT"]),
        ("aapl, aapl ,msft", ["AAPL", "MSFT"]),
        (["AAPL", "MSFT"], ["AAPL", "MSFT"]),
        (None, []),
        ("", []),
        (12345, []),
    ])
    def test_parse_symbols(self, value, expected):
        assert OpenBBScraper._parse_symbols(value) == expected

    def test_ensure_utc_naive(self):
        naive = datetime(2025, 1, 1, 12, 0, 0)
        out = OpenBBScraper._ensure_utc(naive)
        assert out.tzinfo is not None

    def test_ensure_utc_other_tz(self):
        other = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        out = OpenBBScraper._ensure_utc(other)
        assert out.tzinfo == timezone.utc
        assert out.hour == 4

    def test_coerce_datetime_handles_bogus(self):
        assert OpenBBScraper._coerce_datetime("not-a-date") is None
        assert OpenBBScraper._coerce_datetime(42) is None
        assert OpenBBScraper._coerce_datetime(None) is None

    def test_coerce_url_handles_bogus(self):
        assert OpenBBScraper._coerce_url(None) is None
        assert OpenBBScraper._coerce_url("  ") is None
        assert OpenBBScraper._coerce_url("http://x") == "http://x"
