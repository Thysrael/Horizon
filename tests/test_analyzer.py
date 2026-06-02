import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import src.ai.analyzer as analyzer_module
from src.ai.analyzer import ContentAnalyzer
from src.ai.prompts import CONTENT_ANALYSIS_SYSTEM
from src.models import ContentItem, ScoringConfig, SourceType


def _make_item(item_id: str) -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=SourceType.RSS,
        title=f"Item {item_id}",
        url="https://example.com/item",
        published_at=datetime(2026, 4, 26, tzinfo=timezone.utc),
    )


def test_analyze_batch_does_not_sleep_by_default(monkeypatch):
    analyzer = ContentAnalyzer(SimpleNamespace())
    items = [_make_item("rss:test:1"), _make_item("rss:test:2")]
    sleep_calls = []

    async def fake_analyze_item(item):
        item.ai_score = 8.0

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(analyzer, "_analyze_item", fake_analyze_item)
    monkeypatch.setattr(analyzer_module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(analyzer.analyze_batch(items))

    assert len(result) == 2
    assert sleep_calls == []


def test_analyze_batch_sleeps_between_items_when_throttle_configured(monkeypatch):
    client = SimpleNamespace(config=SimpleNamespace(throttle_sec=1.5))
    analyzer = ContentAnalyzer(client)
    items = [_make_item("rss:test:1"), _make_item("rss:test:2"), _make_item("rss:test:3")]
    sleep_calls = []

    async def fake_analyze_item(item):
        item.ai_score = 8.0

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(analyzer, "_analyze_item", fake_analyze_item)
    monkeypatch.setattr(analyzer_module.asyncio, "sleep", fake_sleep)

    asyncio.run(analyzer.analyze_batch(items))

    assert sleep_calls == [1.5, 1.5]


def test_analyze_batch_concurrent_processing(monkeypatch):
    """Verify that higher concurrency allows overlapping item processing."""
    client = SimpleNamespace(config=SimpleNamespace(analysis_concurrency=3))
    analyzer = ContentAnalyzer(client)
    items = [_make_item(f"rss:test:{i}") for i in range(5)]
    active_count = 0
    max_active = 0

    async def fake_analyze_item(item):
        nonlocal active_count, max_active
        active_count += 1
        max_active = max(max_active, active_count)
        await asyncio.sleep(0.05)  # Small delay to allow overlap
        active_count -= 1

    monkeypatch.setattr(analyzer, "_analyze_item", fake_analyze_item)

    asyncio.run(analyzer.analyze_batch(items))

    assert max_active == 3
    assert all(item.ai_score is None for item in items)  # None because fake_analyze_item doesn't set it


def test_analyze_batch_concurrent_preserves_order(monkeypatch):
    """Verify that analyze_batch preserves input order in results."""
    client = SimpleNamespace(config=SimpleNamespace(analysis_concurrency=3))
    analyzer = ContentAnalyzer(client)
    items = [_make_item(f"rss:test:{i}") for i in range(5)]

    async def fake_analyze_item(item):
        item.ai_score = float(item.id.split(":")[-1]) * 10

    monkeypatch.setattr(analyzer, "_analyze_item", fake_analyze_item)

    result = asyncio.run(analyzer.analyze_batch(items))

    assert [item.id for item in result] == [item.id for item in items]


def test_build_system_prompt_without_scoring_uses_base_prompt():
    analyzer = ContentAnalyzer(SimpleNamespace())

    assert analyzer._build_system_prompt() == CONTENT_ANALYSIS_SYSTEM


def test_build_system_prompt_with_empty_scoring_profile_uses_base_prompt():
    scoring = ScoringConfig(profile_name="default")
    analyzer = ContentAnalyzer(SimpleNamespace(), scoring_config=scoring)

    assert analyzer._build_system_prompt() == CONTENT_ANALYSIS_SYSTEM


def test_build_system_prompt_includes_personal_scoring_profile():
    scoring = ScoringConfig(
        profile_name="personal",
        primary=["cognitive value", "paradigm shifts"],
        secondary=["engineering usefulness"],
        boost=["durable mental models"],
        downrank=["generic AI hype"],
        notes="Prefer cognitive value first.",
    )
    analyzer = ContentAnalyzer(SimpleNamespace(), scoring_config=scoring)

    prompt = analyzer._build_system_prompt()

    assert CONTENT_ANALYSIS_SYSTEM in prompt
    assert "Personal scoring profile: personal" in prompt
    assert "Primary high-score signals" in prompt
    assert "- cognitive value" in prompt
    assert "- paradigm shifts" in prompt
    assert "Secondary high-score signals" in prompt
    assert "- engineering usefulness" in prompt
    assert "Boost when content matches" in prompt
    assert "- durable mental models" in prompt
    assert "Downrank when content is" in prompt
    assert "- generic AI hype" in prompt
    assert "Prefer cognitive value first." in prompt
