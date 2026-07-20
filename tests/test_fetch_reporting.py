from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from rich.console import Console

from src.models import ContentItem, SourceType
from src.orchestrator import FetchReport, HorizonOrchestrator, SourceFetchOutcome


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
        return self.result


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


def test_native_run_raises_when_every_attempted_source_failed(monkeypatch) -> None:
    orchestrator = make_orchestrator()
    orchestrator.config = SimpleNamespace(  # type: ignore[assignment]
        email=None,
        filtering=SimpleNamespace(time_window_hours=24),
    )
    orchestrator.email_manager = None
    send_failure = AsyncMock()
    orchestrator.webhook_notifier = SimpleNamespace(send_failure=send_failure)  # type: ignore[assignment]
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
        filtering=SimpleNamespace(time_window_hours=24),
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


def test_native_run_skips_all_delivery_after_successful_empty_fetch(monkeypatch) -> None:
    """Legacy run keeps its historical no-content early exit."""
    orchestrator = make_orchestrator()
    orchestrator.config = SimpleNamespace(  # type: ignore[assignment]
        email=SimpleNamespace(enabled=True, imap_enabled=False),
        filtering=SimpleNamespace(time_window_hours=24),
        ai=SimpleNamespace(languages=["en"]),
    )
    orchestrator.storage = SimpleNamespace(
        save_daily_summary=Mock(), load_subscribers=Mock()
    )
    orchestrator.email_manager = SimpleNamespace(send_daily_summary=Mock())
    send_daily_summary = AsyncMock()
    orchestrator.webhook_notifier = SimpleNamespace(send_daily_summary=send_daily_summary)

    async def fetch_all_sources(since):  # type: ignore[no-untyped-def]
        orchestrator.last_fetch_report = FetchReport(
            [SourceFetchOutcome("RSS Feeds", "empty")]
        )
        return []

    monkeypatch.setattr(orchestrator, "fetch_all_sources", fetch_all_sources)
    monkeypatch.setattr(
        "src.orchestrator.DailySummarizer.generate_summary",
        AsyncMock(return_value="# Empty summary"),
    )
    save_pages_post = Mock()
    monkeypatch.setattr("src.orchestrator.safe_output_path", save_pages_post)

    asyncio.run(orchestrator.run())

    orchestrator.storage.save_daily_summary.assert_not_called()
    save_pages_post.assert_not_called()
    orchestrator.email_manager.send_daily_summary.assert_not_called()
    send_daily_summary.assert_not_awaited()
