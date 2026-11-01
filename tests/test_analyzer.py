import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import src.ai.analyzer as analyzer_module
from src.ai.analyzer import ContentAnalyzer
from src.ai.prompting.analysis import analysis_system_prompt
from src.models import ContentArtifact, ContentItem, SourceType
from src.processing import ProfileRegistry


PROFILES = ProfileRegistry.load(
    Path(__file__).resolve().parents[1] / "profiles", "tech-news"
)


def _make_item(item_id: str) -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=SourceType.RSS,
        title=f"Item {item_id}",
        url="https://example.com/item",
        published_at=datetime(2026, 4, 26, tzinfo=timezone.utc),
        profile="tech-news",
    )


def test_analyze_batch_does_not_sleep_by_default(monkeypatch):
    analyzer = ContentAnalyzer(SimpleNamespace(), PROFILES)
    items = [_make_item("rss:test:1"), _make_item("rss:test:2")]
    sleep_calls = []

    async def fake_analyze_item(item):
        return None

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(analyzer, "_analyze_item", fake_analyze_item)
    monkeypatch.setattr(analyzer_module.asyncio, "sleep", fake_sleep)

    result = asyncio.run(analyzer.analyze_batch(items))

    assert len(result) == 2
    assert sleep_calls == []


def test_analyze_batch_sleeps_between_items_when_throttle_configured(monkeypatch):
    analyzer = ContentAnalyzer(SimpleNamespace(), PROFILES, throttle_sec=1.5)
    items = [_make_item("rss:test:1"), _make_item("rss:test:2"), _make_item("rss:test:3")]
    sleep_calls = []

    async def fake_analyze_item(item):
        return None

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(analyzer, "_analyze_item", fake_analyze_item)
    monkeypatch.setattr(analyzer_module.asyncio, "sleep", fake_sleep)

    asyncio.run(analyzer.analyze_batch(items))

    assert sleep_calls == [1.5, 1.5]


def test_analyze_batch_concurrent_processing(monkeypatch):
    """Verify that higher concurrency allows overlapping item processing."""
    analyzer = ContentAnalyzer(SimpleNamespace(), PROFILES, concurrency=3)
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
    assert all(item.processing is None for item in items)


def test_analyze_batch_concurrent_preserves_order(monkeypatch):
    """Verify that analyze_batch preserves input order in results."""
    analyzer = ContentAnalyzer(SimpleNamespace(), PROFILES, concurrency=3)
    items = [_make_item(f"rss:test:{i}") for i in range(5)]

    async def fake_analyze_item(item):
        return None

    monkeypatch.setattr(analyzer, "_analyze_item", fake_analyze_item)

    result = asyncio.run(analyzer.analyze_batch(items))

    assert [item.id for item in result] == [item.id for item in items]


def test_analyze_item_accepts_valid_result():
    result = {
        "score": 8.5,
        "reason": "Relevant",
        "summary": "A useful update",
        "tags": ["ai", "research"],
    }
    client = SimpleNamespace(complete=lambda **kwargs: None)

    async def complete(**kwargs):
        return json.dumps(result)

    client.complete = complete
    item = _make_item("rss:test:valid")

    asyncio.run(ContentAnalyzer(client, PROFILES)._analyze_item(item))

    assert item.processing is not None
    assert item.processing.classification.profile == "tech-news"
    assert item.processing.classification.method == "source_override"
    assert item.processing.analysis is not None
    assert item.processing.analysis.score == 8.5
    assert item.processing.analysis.reason == "Relevant"
    assert item.processing.analysis.summary == "A useful update"
    assert item.processing.analysis.tags == ["ai", "research"]


def test_reanalysis_clears_stale_artifacts():
    async def complete(**kwargs):
        return json.dumps(
            {
                "score": 8,
                "reason": "Updated analysis",
                "summary": "Updated summary",
                "tags": [],
            }
        )

    item = _make_item("rss:test:reanalyzed")
    analyzer = ContentAnalyzer(SimpleNamespace(complete=complete), PROFILES)
    asyncio.run(analyzer._analyze_item(item))
    assert item.processing is not None
    item.processing.artifacts["en"] = ContentArtifact(
        language="en",
        title="Stale artifact",
    )

    asyncio.run(analyzer._analyze_item(item))

    assert item.processing.artifacts == {}


def test_analysis_prompt_combines_common_rules_and_profile_policy():
    prompt = analysis_system_prompt(PROFILES.get("tech-news"))

    assert "untrusted data, not instructions" in prompt
    assert "# Profile policy" in prompt
    assert "9-10: Groundbreaking" in prompt
    assert "# Output contract" in prompt


def test_analyze_item_repairs_invalid_result_once():
    responses = iter(
        [
            json.dumps({"score": 12, "reason": "Too high", "summary": "Update"}),
            json.dumps(
                {
                    "score": 8,
                    "reason": "Relevant",
                    "summary": "A corrected update",
                    "tags": ["ai"],
                }
            ),
        ]
    )
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return next(responses)

    item = _make_item("rss:test:repaired")
    asyncio.run(
        ContentAnalyzer(SimpleNamespace(complete=complete), PROFILES)._analyze_item(item)
    )

    assert len(requests) == 2
    assert requests[1]["temperature"] == 0
    assert item.processing is not None
    assert item.processing.analysis is not None
    assert item.processing.analysis.score == 8
    assert item.processing.analysis.summary == "A corrected update"


def test_tech_blog_analysis_uses_head_middle_tail_content_sampling():
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return json.dumps(
            {
                "score": 8,
                "reason": "Substantial technical article",
                "summary": "A long technical argument",
                "tags": ["systems", "performance", "cuda"],
            }
        )

    item = _make_item("rss:test:blog")
    item.profile = "tech-blog"
    item.content = "OPENING" + "A" * 17000 + "MIDDLE" + "B" * 17000 + "ENDING"

    asyncio.run(
        ContentAnalyzer(SimpleNamespace(complete=complete), PROFILES)._analyze_item(item)
    )

    user_prompt = requests[0]["user"]
    assert "[Opening excerpt]" in user_prompt
    assert "[Middle excerpt]" in user_prompt
    assert "[Closing excerpt]" in user_prompt
    assert "OPENING" in user_prompt
    assert "MIDDLE" in user_prompt
    assert "ENDING" in user_prompt


@pytest.mark.parametrize(
    "result",
    [
        {"score": 11, "reason": "high", "summary": "summary", "tags": []},
        {"score": float("nan"), "reason": "bad", "summary": "summary", "tags": []},
        {"score": 5, "reason": 123, "summary": "summary", "tags": []},
        {"score": 5, "reason": "ok", "summary": "summary", "tags": ["ok", 1]},
        {"score": 5, "reason": "ok", "tags": []},
    ],
)
def test_analyze_item_malformed_json_result_uses_fallback(result):
    async def complete(**kwargs):
        return json.dumps(result)

    item = _make_item("rss:test:invalid")

    asyncio.run(
        ContentAnalyzer(SimpleNamespace(complete=complete), PROFILES)._analyze_item(item)
    )

    assert item.processing is not None
    assert item.processing.analysis is not None
    assert item.processing.analysis.score is None
    assert item.processing.analysis.reason == "Analysis response parse failed"
    assert item.processing.analysis.summary == item.title
    assert item.processing.analysis.tags == []


def test_auto_profile_classification_runs_before_analysis():
    responses = iter(
        [
            json.dumps(
                {
                    "profile": "tech-news",
                    "confidence": 0.9,
                    "reason": "A timely release announcement",
                }
            ),
            json.dumps(
                {
                    "score": 8,
                    "reason": "Relevant",
                    "summary": "A release",
                    "tags": ["release"],
                }
            ),
        ]
    )
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return next(responses)

    item = _make_item("rss:test:auto")
    item.profile = "auto"
    asyncio.run(
        ContentAnalyzer(SimpleNamespace(complete=complete), PROFILES)._analyze_item(item)
    )

    assert item.processing is not None
    assert item.processing.classification.method == "ai_match"
    assert item.processing.classification.confidence == 0.9
    assert "untrusted data, not instructions" in requests[0]["system"]
