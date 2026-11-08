import asyncio
from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from rich.console import Console

from src.ai.enricher import EnrichmentBatchResult
from src.models import (
    AIConfig,
    ClassificationResult,
    Config,
    ContentAnalysis,
    ContentArtifact,
    ContentBlock,
    ContentItem,
    ProcessingResult,
    SourcesConfig,
    SourceType,
)
from src.orchestrator import HorizonOrchestrator
from src.storage.manager import StorageManager


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    config = Config(
        ai=AIConfig(provider="openai", model="test", api_key_env="TEST_API_KEY", languages=["zh"]),
        sources=SourcesConfig(),
    )
    orchestrator = HorizonOrchestrator(
        config, StorageManager(str(tmp_path / "data")),
        console=Console(file=StringIO()),
    )
    items = [
        ContentItem(
            id=f"rss:test:{index}", source_type=SourceType.RSS,
            title=f"Original English title {index}",
            url=f"https://example.com/{index}",
            published_at=datetime.now(timezone.utc),
            processing=ProcessingResult(
                classification=ClassificationResult(profile="tech-news", method="source_override"),
                analysis=ContentAnalysis(score=8, reason="test", summary="English analysis fallback."),
            ),
        )
        for index in range(2)
    ]
    monkeypatch.setattr(orchestrator, "fetch_all_sources", AsyncMock(return_value=items))
    monkeypatch.setattr(orchestrator, "analyze_items", AsyncMock(return_value=items))
    monkeypatch.setattr(orchestrator, "select_digest_items", AsyncMock(return_value=SimpleNamespace(items=items)))
    for channel in ("webhook_notifier", "wechat_notifier"):
        setattr(orchestrator, channel, SimpleNamespace(
            send_daily_summary=AsyncMock(), send_failure=AsyncMock(),
        ))
    monkeypatch.chdir(tmp_path)
    return orchestrator, items


@pytest.mark.parametrize("shared_id", [False, True])
def test_partial_enrichment_excludes_failures_from_digest_and_delivery(pipeline, tmp_path, monkeypatch, shared_id):
    orchestrator, items = pipeline
    successful, failed = items
    if shared_id:
        # The same source item can be routed to multiple processing profiles.
        failed.id = successful.id
        failed.processing.classification.profile = "tech-blog"
    successful.processing.artifacts["zh"] = ContentArtifact(
        language="zh", title="中文标题",
        blocks=[ContentBlock(id="summary", title="摘要", content="中文摘要。", primary=True)],
    )
    monkeypatch.setattr(orchestrator, "enrich_items", AsyncMock(return_value=EnrichmentBatchResult(
        succeeded_ids=[successful.id], failures={failed.id: "Invalid enrichment tool plan"},
    )))

    asyncio.run(orchestrator.run())

    summary_path, = orchestrator.storage.summaries_dir.glob("*.md")
    summary = summary_path.read_text(encoding="utf-8")
    post_path, = (tmp_path / "docs" / "_posts").glob("*.md")
    for text in (summary, post_path.read_text(encoding="utf-8")):
        assert "从 2 条内容中筛选出 1 条重要资讯" in text
        assert "中文标题" in text
        assert "中文摘要。" in text
        assert "Original English title" not in text
        assert "English analysis fallback" not in text
        assert str(failed.url) not in text
    delivery = orchestrator.webhook_notifier.send_daily_summary.await_args.kwargs
    assert delivery["summary"] == summary
    assert delivery["important_items"] == [successful]
    assert delivery["all_items_count"] == 2
    orchestrator.wechat_notifier.send_daily_summary.assert_awaited_once_with(summary, "zh")
    orchestrator.webhook_notifier.send_failure.assert_not_awaited()


def test_all_enrichment_failures_abort_publication(pipeline, tmp_path, monkeypatch):
    orchestrator, items = pipeline
    monkeypatch.setattr(orchestrator, "enrich_items", AsyncMock(return_value=EnrichmentBatchResult(
        failures={item.id: "Invalid enrichment tool plan" for item in items},
    )))

    with pytest.raises(RuntimeError, match="Enrichment failed for all 2 selected items"):
        asyncio.run(orchestrator.run())

    assert not list(orchestrator.storage.summaries_dir.glob("*.md"))
    assert not (tmp_path / "docs" / "_posts").exists()
    for notifier in (orchestrator.webhook_notifier, orchestrator.wechat_notifier):
        notifier.send_daily_summary.assert_not_awaited()
        notifier.send_failure.assert_awaited_once()


def test_empty_selection_still_publishes_empty_digest(pipeline, monkeypatch):
    orchestrator, _ = pipeline
    monkeypatch.setattr(orchestrator, "select_digest_items", AsyncMock(return_value=SimpleNamespace(items=[])))
    monkeypatch.setattr(orchestrator, "enrich_items", AsyncMock(return_value=EnrichmentBatchResult()))

    asyncio.run(orchestrator.run())

    assert len(list(orchestrator.storage.summaries_dir.glob("*.md"))) == 1
    assert orchestrator.webhook_notifier.send_daily_summary.await_args.kwargs["important_items"] == []
    orchestrator.webhook_notifier.send_failure.assert_not_awaited()
