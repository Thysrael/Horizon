from datetime import datetime, timezone
import json

from src.models import ContentItem, SourceType
from types import SimpleNamespace

import pytest
from rich.console import Console

from src.models import AIConfig, CategoryGroupConfig, Config, FilteringConfig, SourcesConfig
from src.orchestrator import HorizonOrchestrator
from src.storage.manager import StorageManager


def make_item(item_id: str, score: float | None = None) -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=SourceType.TWITTER,
        title=f"title {item_id}",
        url=f"https://x.com/user/status/{item_id}",
        content="body",
        author="user",
        published_at=datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc),
        ai_score=score,
        ai_reason="reason" if score is not None else None,
        metadata={"category": "ai-tools"},
    )


def test_save_run_artifact_writes_jsonl_with_scores(tmp_path):
    storage = StorageManager(data_dir=str(tmp_path))

    path = storage.save_run_artifact("2026-06-30T120000Z", "analyzed", [make_item("1", 7.5)])

    assert path == tmp_path / "runs" / "2026-06-30T120000Z" / "analyzed.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "1"
    assert row["source_type"] == "twitter"
    assert row["url"] == "https://x.com/user/status/1"
    assert row["published_at"] == "2026-06-30T12:00:00Z"
    assert row["fetched_at"].endswith("Z")
    assert row["ai_score"] == 7.5
    assert row["ai_reason"] == "reason"
    assert row["metadata"] == {"category": "ai-tools"}


def test_orchestrator_persists_auditable_run_stages(monkeypatch, tmp_path):
    config = Config(
        ai=AIConfig(
            provider="openai",
            model="test",
            api_key_env="TEST_API_KEY",
            languages=[],
        ),
        sources=SourcesConfig(),
        filtering=FilteringConfig(
            ai_score_threshold=6.0,
            max_items=1,
            category_groups={"ai": CategoryGroupConfig(limit=1, categories=["ai-tools"])},
            default_group_limit=1,
        ),
    )
    storage = StorageManager(data_dir=str(tmp_path))
    orchestrator = HorizonOrchestrator(config, storage)
    orchestrator.console = Console(record=True)

    raw_items = [make_item("selected", 9.0), make_item("rejected", 4.0)]
    raw_items[0].metadata["category"] = "ai-tools"
    raw_items[1].metadata["category"] = "ai-tools"

    async def fetch_all_sources(since):
        return raw_items

    async def analyze_content(input_items):
        return input_items

    async def merge_topic_duplicates(input_items):
        return input_items

    async def expand_twitter_discussion(input_items):
        return None

    async def enrich_important_items(input_items):
        return None

    monkeypatch.setattr(orchestrator, "fetch_all_sources", fetch_all_sources)
    monkeypatch.setattr(orchestrator, "_analyze_content", analyze_content)
    monkeypatch.setattr(orchestrator, "merge_topic_duplicates", merge_topic_duplicates)
    monkeypatch.setattr(orchestrator, "_expand_twitter_discussion", expand_twitter_discussion)
    monkeypatch.setattr(orchestrator, "_enrich_important_items", enrich_important_items)
    monkeypatch.setattr(orchestrator, "_run_id", lambda: "run-1")
    monkeypatch.chdir(tmp_path)

    import asyncio

    asyncio.run(orchestrator.run())

    run_dir = tmp_path / "runs" / "run-1"
    assert sorted(p.name for p in run_dir.glob("*.jsonl")) == [
        "analyzed.jsonl",
        "important.jsonl",
        "merged.jsonl",
        "raw.jsonl",
        "rejected.jsonl",
        "selected.jsonl",
    ]
    selected_rows = [json.loads(line) for line in (run_dir / "selected.jsonl").read_text().splitlines()]
    rejected_rows = [json.loads(line) for line in (run_dir / "rejected.jsonl").read_text().splitlines()]
    assert [row["id"] for row in selected_rows] == ["selected"]
    assert [row["id"] for row in rejected_rows] == ["rejected"]
