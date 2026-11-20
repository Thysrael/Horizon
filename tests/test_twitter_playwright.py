"""Offline tests for Playwright Twitter cookie-isolation behaviour."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.models import TwitterConfig
from src.scrapers import twitter_playwright
from src.scrapers.base import FetchResult
from src.scrapers.twitter_playwright import _load_valid_cookie_sets

SINCE = datetime(2026, 11, 1, tzinfo=timezone.utc)


def test_invalid_cookie_file_does_not_block_later_valid_file(tmp_path):
    invalid = tmp_path / "x_cookies_bad.json"
    valid = tmp_path / "x_cookies_good.json"
    invalid.write_text("{", encoding="utf-8")
    valid.write_text(
        json.dumps([{"name": "auth_token", "value": "placeholder", "domain": ".x.com"}]),
        encoding="utf-8",
    )
    result = FetchResult()

    cookie_sets = _load_valid_cookie_sets([invalid, valid], result)

    assert cookie_sets == [
        (1, [{"name": "auth_token", "value": "placeholder", "domain": ".x.com", "path": "/", "secure": True, "httpOnly": False}])
    ]
    assert set(result.failures) == {"cookie_file_1"}
    assert "placeholder" not in str(result.failures)


class _FakePage:
    def __init__(self):
        self.goto = AsyncMock()
        self.close = AsyncMock()


class _FakeContext:
    def __init__(self):
        self.add_cookies = AsyncMock()
        self.new_page = AsyncMock(return_value=_FakePage())
        self.close = AsyncMock()


class _FakeBrowser:
    def __init__(self):
        self.contexts: list[_FakeContext] = []
        self.new_context = AsyncMock(side_effect=self._new_context)
        self.close = AsyncMock()

    def _new_context(self, **kwargs):
        context = _FakeContext()
        context.user_agent = kwargs.get("user_agent")
        self.contexts.append(context)
        return context


class _FakeStealthContext:
    def __init__(self, playwright):
        self._playwright = playwright

    async def __aenter__(self):
        return self._playwright

    async def __aexit__(self, *exc_info):
        return False


class _FakeStealth:
    def __init__(self, playwright):
        self._playwright = playwright

    def use_async(self, _playwright_manager):
        return _FakeStealthContext(self._playwright)


class _FakeAsyncio:
    """Delegate to the real asyncio module but skip real waiting."""

    sleep = AsyncMock()

    def __getattr__(self, name):
        return getattr(asyncio, name)


def _install_fake_playwright(monkeypatch, browser: _FakeBrowser):
    """Replace Playwright with in-memory fakes so no browser is ever launched."""
    playwright = SimpleNamespace(
        chromium=SimpleNamespace(launch=AsyncMock(return_value=browser))
    )
    monkeypatch.setattr(twitter_playwright, "PLAYWRIGHT_AVAILABLE", True)
    monkeypatch.setattr(
        twitter_playwright, "Stealth", lambda: _FakeStealth(playwright)
    )
    monkeypatch.setattr(
        twitter_playwright, "async_playwright", lambda: SimpleNamespace()
    )
    monkeypatch.setattr(twitter_playwright, "asyncio", _FakeAsyncio())
    return playwright


def _make_scraper(cookie_dir, users=("karpathy",)):
    config = TwitterConfig(
        enabled=True,
        mode="playwright",
        users=list(users),
        cookie_dir=str(cookie_dir),
    )
    return twitter_playwright.TwitterPlaywrightScraper(config)


def test_all_cookie_files_invalid_retains_failures_without_launching(monkeypatch, tmp_path):
    (tmp_path / "x_cookies_a.json").write_text("{", encoding="utf-8")
    (tmp_path / "x_cookies_b.json").write_text(
        json.dumps([{"value": "placeholder", "domain": ".x.com"}]), encoding="utf-8"
    )

    browser = _FakeBrowser()
    playwright = _install_fake_playwright(monkeypatch, browser)
    scraper = _make_scraper(tmp_path)

    scraped: list[str] = []

    async def fake_scrape_user(ctx, username, since):
        scraped.append(username)
        return []

    monkeypatch.setattr(scraper, "_scrape_user", fake_scrape_user)

    result = asyncio.run(scraper.fetch(SINCE))

    assert set(result.failures) == {"cookie_file_1", "cookie_file_2"}
    assert all("Invalid cookie file" in msg for msg in result.failures.values())
    assert "placeholder" not in str(result.failures)
    assert result.status == "failure"
    assert playwright.chromium.launch.await_count == 0
    assert browser.new_context.await_count == 0
    assert scraped == []


def test_valid_cookie_file_after_malformed_one_keeps_original_numbering(
    monkeypatch, tmp_path, caplog
):
    (tmp_path / "x_cookies_a.json").write_text("{", encoding="utf-8")
    (tmp_path / "x_cookies_b.json").write_text(
        json.dumps([{"name": "auth_token", "value": "placeholder", "domain": ".x.com"}]),
        encoding="utf-8",
    )

    browser = _FakeBrowser()
    _install_fake_playwright(monkeypatch, browser)
    scraper = _make_scraper(tmp_path)

    scraped: list[str] = []

    async def fake_scrape_user(ctx, username, since):
        scraped.append(username)
        return [
            {
                "tweet_id": "1",
                "text": "hello",
                "datetime": "2026-11-01T00:00:00+00:00",
            }
        ]

    monkeypatch.setattr(scraper, "_scrape_user", fake_scrape_user)

    with caplog.at_level(logging.INFO, logger="src.scrapers.twitter_playwright"):
        result = asyncio.run(scraper.fetch(SINCE))

    assert set(result.failures) == {"cookie_file_1"}
    assert scraped == ["karpathy"]
    assert len(browser.contexts) == 1
    browser.contexts[0].add_cookies.assert_awaited_once()
    # Cookie-file index 1 (the second file) still drives the profile string.
    assert "Chrome/131.0.0.0" in browser.contexts[0].user_agent
    assert len(result.items) == 1
    assert result.successful == 1
    # Diagnostics keep the numbering of the configured cookie files, not the
    # index of the surviving entry.
    assert "Cookie #2 warm-up done" in caplog.text
    assert "with cookie #2" in caplog.text
    assert "with cookie #1" not in caplog.text
    browser.close.assert_awaited_once()
