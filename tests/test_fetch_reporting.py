from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import httpx
from rich.console import Console

from src.models import ContentItem, SourceType
from src.orchestrator import FetchReport, HorizonOrchestrator, SourceFetchOutcome
from src.scrapers.base import FetchResult
from src.scrapers.github import GitHubScraper
from src.scrapers.hackernews import HackerNewsScraper
from src.scrapers.rss import RSSScraper
from src.scrapers.reddit import RedditScraper
from src.scrapers.telegram import TelegramScraper
from src.scrapers.gdelt import GDELTScraper
from src.scrapers.google_news import GoogleNewsScraper
from src.scrapers.ossinsight import OSSInsightScraper
from src.models import (
    GitHubSourceConfig, HackerNewsConfig, RSSSourceConfig, RedditConfig,
    RedditSubredditConfig, TelegramConfig, TelegramChannelConfig, GDELTConfig,
    GoogleNewsConfig, OSSInsightConfig,
)


SINCE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_item(item_id: str) -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=SourceType.RSS,
        title=item_id,
        url=f"https://example.com/{item_id}",
        content="content",
        author="tester",
        published_at=SINCE,
    )


def make_orchestrator() -> HorizonOrchestrator:
    orchestrator = object.__new__(HorizonOrchestrator)
    orchestrator.console = Console(file=StringIO())
    orchestrator.last_fetch_report = None
    orchestrator.webhook_notifier = None
    orchestrator.wechat_notifier = None
    return orchestrator


def make_sources(**overrides):  # type: ignore[no-untyped-def]
    values = {
        "github": [],
        "hackernews": SimpleNamespace(enabled=False),
        "rss": [],
        "reddit": SimpleNamespace(enabled=False),
        "telegram": SimpleNamespace(enabled=False),
        "twitter": None,
        "openbb": None,
        "ossinsight": SimpleNamespace(enabled=False),
        "gdelt": None,
        "google_news": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class StubScraper:
    def __init__(self, result=None, error: Exception | None = None):  # type: ignore[no-untyped-def]
        self.result = [] if result is None else result
        self.error = error

    async def fetch(self, since):  # type: ignore[no-untyped-def]
        if self.error:
            raise self.error
        return FetchResult(items=self.result, successful=1)


def test_all_success_empty_has_normal_success_report(monkeypatch) -> None:
    orchestrator = make_orchestrator()
    orchestrator.config = SimpleNamespace(  # type: ignore[assignment]
        sources=make_sources(github=[object()]), extractors={}
    )
    monkeypatch.setattr(
        "src.orchestrator.GitHubScraper",
        lambda config, client: StubScraper(),
    )

    items = asyncio.run(orchestrator.fetch_all_sources(SINCE))

    assert items == []
    assert orchestrator.last_fetch_report is not None
    assert orchestrator.last_fetch_report.status == "success"
    assert orchestrator.last_fetch_report.all_failed is False
    assert orchestrator.last_fetch_report.to_dict()["empty"] == 1


def test_partial_failure_keeps_items_and_source_names(monkeypatch) -> None:
    orchestrator = make_orchestrator()
    kept = make_item("kept")
    orchestrator.config = SimpleNamespace(  # type: ignore[assignment]
        sources=make_sources(
            github=[object()], hackernews=SimpleNamespace(enabled=True)
        ),
        extractors={},
    )
    monkeypatch.setattr(
        "src.orchestrator.GitHubScraper",
        lambda config, client: StubScraper([kept]),
    )
    monkeypatch.setattr(
        "src.orchestrator.HackerNewsScraper",
        lambda config, client: StubScraper(error=ValueError("unavailable")),
    )

    items = asyncio.run(orchestrator.fetch_all_sources(SINCE))

    assert items == [kept]
    assert orchestrator.last_fetch_report is not None
    report = orchestrator.last_fetch_report
    assert [outcome.source_name for outcome in report.outcomes] == ["GitHub", "Hacker News"]
    assert report.status == "partial_failure"
    assert report.failed_count == 1
    source_reports = report.to_dict()["sources"]
    assert isinstance(source_reports, list)
    assert source_reports[1]["error"] == "ValueError: unavailable"


@pytest.mark.parametrize("channel", ["webhook_notifier", "wechat_notifier"])
def test_native_run_raises_when_every_attempted_source_failed(monkeypatch, channel) -> None:
    orchestrator = make_orchestrator()
    orchestrator.config = SimpleNamespace(  # type: ignore[assignment]
        email=None,
        collection=SimpleNamespace(time_window_hours=24),
    )
    orchestrator.email_manager = None
    send_failure = AsyncMock()
    setattr(orchestrator, channel, SimpleNamespace(send_failure=send_failure))
    report = FetchReport(
        [
            SourceFetchOutcome("GitHub", "failure", error="RuntimeError: down"),
            SourceFetchOutcome("RSS Feeds", "failure", error="TimeoutError: slow"),
        ]
    )

    async def fetch_all_sources(since):  # type: ignore[no-untyped-def]
        orchestrator.last_fetch_report = report
        return []

    monkeypatch.setattr(orchestrator, "fetch_all_sources", fetch_all_sources)

    with pytest.raises(RuntimeError, match="All 2 attempted sources failed.*GitHub.*RSS Feeds"):
        asyncio.run(orchestrator.run())

    send_failure.assert_awaited_once()


def test_native_run_treats_all_success_empty_as_no_content(monkeypatch) -> None:
    orchestrator = make_orchestrator()
    orchestrator.config = SimpleNamespace(  # type: ignore[assignment]
        email=None,
        collection=SimpleNamespace(time_window_hours=24),
    )
    orchestrator.email_manager = None
    send_failure = AsyncMock()
    orchestrator.webhook_notifier = SimpleNamespace(send_failure=send_failure)  # type: ignore[assignment]

    async def fetch_all_sources(since):  # type: ignore[no-untyped-def]
        orchestrator.last_fetch_report = FetchReport(
            [SourceFetchOutcome("RSS Feeds", "empty")]
        )
        return []

    monkeypatch.setattr(orchestrator, "fetch_all_sources", fetch_all_sources)

    asyncio.run(orchestrator.run())

    send_failure.assert_not_awaited()


@pytest.mark.parametrize("scraper_type,config,empty_payload", [
    (HackerNewsScraper, HackerNewsConfig(), []),
    (GitHubScraper, [GitHubSourceConfig(type="user_events", username="test")], []),
    (RSSScraper, [RSSSourceConfig(name="feed", url="https://example.com/feed")], "<rss version='2.0'><channel/></rss>"),
    (RedditScraper, RedditConfig(subreddits=[RedditSubredditConfig(subreddit="test")]), {"data": {"children": []}}),
    (TelegramScraper, TelegramConfig(channels=[TelegramChannelConfig(channel="test")]), "<html></html>"),
    (GDELTScraper, GDELTConfig(enabled=True), {"articles": []}),
    (GoogleNewsScraper, GoogleNewsConfig(enabled=True), "<rss version='2.0'><channel/></rss>"),
    (OSSInsightScraper, OSSInsightConfig(enabled=True, languages=["Python"]), {"data": {"rows": []}}),
])
@pytest.mark.parametrize("status_code", [200, 503])
def test_real_scrapers_distinguish_empty_responses_from_http_failure(scraper_type, config, empty_payload, status_code):
    def handle(request):
        if isinstance(empty_payload, str):
            return httpx.Response(status_code, text=empty_payload)
        return httpx.Response(status_code, json=empty_payload)

    async def fetch():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            return await make_orchestrator()._fetch_with_progress(
                scraper_type.__name__, scraper_type(config, client), SINCE
            )

    outcome = asyncio.run(fetch())
    report = FetchReport([outcome])
    assert outcome.items == []
    if status_code == 503:
        assert outcome.status == "failure"
        assert outcome.failures
        assert report.status == "failure"
        assert report.all_failed
    else:
        assert outcome.status == "empty"
        assert not outcome.failures
        assert report.status == "success"
        assert not report.all_failed


@pytest.mark.parametrize("has_items", [False, True])
def test_rss_partial_failure_keeps_successful_feed_and_diagnostics(has_items):
    entry = """
    <item><title>Story</title><link>https://example.com/story</link>
    <pubDate>Thu, 01 Jan 2026 12:00:00 GMT</pubDate></item>
    """ if has_items else ""

    def handle(request):
        if request.url.path == "/bad":
            return httpx.Response(503)
        return httpx.Response(200, text=f"<rss version='2.0'><channel>{entry}</channel></rss>")

    async def fetch():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            scraper = RSSScraper([
                RSSSourceConfig(name="bad", url="https://example.com/bad"),
                RSSSourceConfig(name="good", url="https://example.com/good"),
            ], client)
            return await make_orchestrator()._fetch_with_progress("RSS", scraper, SINCE)

    outcome = asyncio.run(fetch())
    report = FetchReport([outcome])
    assert outcome.status == "partial_failure"
    assert len(outcome.items) == int(has_items)
    assert set(outcome.failures) == {"bad"}
    assert report.status == "partial_failure"
    assert not report.all_failed
    assert report.to_dict()["partial_failure"] == 1


def test_hackernews_reports_failed_story_requests_without_dropping_other_stories():
    def handle(request):
        if request.url.path.endswith("topstories.json"):
            return httpx.Response(200, json=[1, 2])
        if request.url.path.endswith("1.json"):
            return httpx.Response(503)
        return httpx.Response(200, json={
            "id": 2, "title": "Story", "score": 200, "time": SINCE.timestamp(),
            "url": "https://example.com/story",
        })

    async def fetch():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            return await HackerNewsScraper(HackerNewsConfig(), client).fetch(SINCE)

    result = asyncio.run(fetch())
    assert result.status == "partial_failure"
    assert [item.id for item in result.items] == ["hackernews:story:2"]
    assert set(result.failures) == {"story:1"}
