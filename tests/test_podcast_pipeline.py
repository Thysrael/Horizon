"""Podcast configuration reaches native collection, routing, and filtering."""

import asyncio
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from rich.console import Console

from src.models import Config, ContentItem, PodcastSourceConfig, SourceType
from src.orchestrator import HorizonOrchestrator
from src.scrapers.base import FetchResult
from src.setup.wizard import _count_sources, merge_configs
from src.storage.manager import StorageManager


def config(**sources):
    return Config.model_validate({
        "ai": {"provider": "openai", "model": "test", "api_key_env": "TEST_KEY"},
        "sources": {
            "hackernews": {"enabled": False},
            "reddit": {"enabled": False},
            "telegram": {"enabled": False},
            "ossinsight": {"enabled": False},
            **sources,
        },
    })


def test_opt_in_and_config_bounds():
    assert config().sources.podcast == []
    source = PodcastSourceConfig(name="Interview", url="https://example.com/feed")
    assert source.profile == "podcast"
    for overrides in ({"max_items": 0}, {"max_items": 101}, {"max_transcript_chars": 999}):
        with pytest.raises(ValidationError):
            PodcastSourceConfig(name="Interview", url="https://example.com/feed", **overrides)


def test_podcast_collection_is_wired_with_partial_failure_report(tmp_path, monkeypatch):
    settings = config(podcast=[{"name": "Interviews", "url": "https://example.com/feed"}])
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item = ContentItem(
        id="podcast:episode:one", source_type=SourceType.PODCAST,
        url="https://example.com/episode", title="Interview", content="Transcript",
        published_at=since, profile="podcast", metadata={"feed_name": "Interviews"},
    )
    fetch = AsyncMock(return_value=FetchResult(
        items=[item], successful=1, failures={"Interviews:two": "Missing transcript"},
    ))
    scraper = type("Stub", (), {"fetch": fetch})()
    calls = []

    def factory(sources, client):
        calls.append(sources)
        return scraper

    monkeypatch.setattr("src.orchestrator.PodcastScraper", factory)
    orchestrator = HorizonOrchestrator(
        settings, StorageManager(str(tmp_path / "data")), console=Console(file=StringIO()),
    )
    result = asyncio.run(orchestrator.fetch_all_sources(since))
    assert result == [item]
    assert calls == [settings.sources.podcast]
    fetch.assert_awaited_once_with(since)
    assert orchestrator.last_fetch_report.status == "partial_failure"
    assert "Missing transcript" in str(orchestrator.last_fetch_report.to_dict())
    assert orchestrator._sub_source_label(item) == "Interviews"


def test_wizard_merge_preserves_disabled_podcasts_and_counts_new_feeds():
    existing = config(podcast=[{"name": "Old", "url": "https://example.com/a", "enabled": False}])
    new = config(podcast=[
        {"name": "Same", "url": "https://example.com/a"},
        {"name": "New", "url": "https://example.com/b"},
    ])
    merged = merge_configs(new, existing)
    assert [source.name for source in merged.sources.podcast] == ["Old", "New"]
    assert not merged.sources.podcast[0].enabled
    assert _count_sources(merged) == 1
