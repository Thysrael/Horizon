from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.infoservice.execution.contracts import ReportExecutionRequest
from src.infoservice.execution.horizon import HorizonReportExecutor
from src.models import ContentItem, SourceType


def _item(index: int, *, category: str | None = None, title: str | None = None) -> ContentItem:
    return ContentItem(
        id=f"rss:item-{index}",
        source_type=SourceType.RSS,
        title=title or f"Item {index}",
        url=f"https://example.com/{index}",
        published_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
        metadata={"category": category} if category is not None else {},
    )


@pytest.mark.asyncio
async def test_executor_returns_data_without_file_delivery(tmp_path, monkeypatch):
    config = SimpleNamespace(
        sources=[SimpleNamespace(source_type="rss", enabled=True, config={"name": "Feed", "url": "https://example.com/feed"})],
        language="en",
        ai_score_threshold=7.0,
        max_items=10,
        categories=[],
        exclusions=[],
    )
    request = ReportExecutionRequest(
        report_id=uuid4(), config=config, api_key="sk-user-key", lookback_hours=6
    )

    class FakeOrchestrator:
        def __init__(self, config, storage, runtime_api_key):
            assert config.ai.provider.value == "deepseek"
            assert config.ai.api_key_env == ""
            assert runtime_api_key == "sk-user-key"

        async def execute(self, force_hours=None, custom_instruction=None):
            assert force_hours == 6
            return SimpleNamespace(
                summaries={"en": "# Horizon Daily - 2026-07-20"},
                important_items=[_item(1)],
                all_items_count=2,
                fetch_report={"status": "success"},
                usage={"total_tokens": 3},
            )

    monkeypatch.setattr("src.infoservice.execution.horizon.HorizonOrchestrator", FakeOrchestrator)

    result = await HorizonReportExecutor(model="deepseek-v4-flash", storage=SimpleNamespace(data_dir=tmp_path)).execute(request)

    assert result.markdown.startswith("#")
    assert result.all_items_count == 2
    assert len(result.items) == 1
    assert result.fetch_report == {"status": "success"}
    assert not list(tmp_path.rglob("*.md"))


@pytest.mark.asyncio
async def test_executor_keeps_only_selected_report_categories(tmp_path, monkeypatch):
    config = SimpleNamespace(
        sources=[],
        language="en",
        ai_score_threshold=7.0,
        max_items=10,
        categories=["ai"],
        exclusions=[],
    )
    request = ReportExecutionRequest(report_id=uuid4(), config=config, api_key="sk-user-key")

    class FakeOrchestrator:
        def __init__(self, config, storage, runtime_api_key):
            pass

        async def execute(self, force_hours=None, custom_instruction=None, item_filter=None):
            assert item_filter is not None
            items = [
                _item(1, category="ai", title="AI release"),
                _item(2, category="security", title="Security patch"),
            ]
            selected = [item for item in items if item_filter(item)]
            return SimpleNamespace(
                summaries={"en": "\n".join(item.title for item in selected)},
                important_items=selected,
                all_items_count=len(items),
                fetch_report={"status": "success"},
                usage={},
            )

    monkeypatch.setattr("src.infoservice.execution.horizon.HorizonOrchestrator", FakeOrchestrator)

    result = await HorizonReportExecutor(storage=SimpleNamespace(data_dir=tmp_path)).execute(request)

    assert [item.title for item in result.items] == ["AI release"]
    assert result.markdown == "AI release"


@pytest.mark.asyncio
async def test_executor_excludes_matching_topic_or_category(tmp_path, monkeypatch):
    config = SimpleNamespace(
        sources=[],
        language="en",
        ai_score_threshold=7.0,
        max_items=10,
        categories=[],
        exclusions=["politics", "sponsored"],
    )
    request = ReportExecutionRequest(
        report_id=uuid4(),
        config=config,
        api_key="sk-user-key",
        custom_instruction="Prefer engineering details.",
    )

    class FakeOrchestrator:
        def __init__(self, config, storage, runtime_api_key):
            pass

        async def execute(self, force_hours=None, custom_instruction=None, item_filter=None):
            assert custom_instruction == "Prefer engineering details."
            assert item_filter is not None
            items = [
                _item(1, category="politics", title="Policy update"),
                _item(2, category="ai", title="Sponsored AI launch"),
                _item(3, category="ai", title="Compiler release"),
            ]
            selected = [item for item in items if item_filter(item)]
            return SimpleNamespace(
                summaries={"en": "\n".join(item.title for item in selected)},
                important_items=selected,
                all_items_count=len(items),
                fetch_report={"status": "success"},
                usage={},
            )

    monkeypatch.setattr("src.infoservice.execution.horizon.HorizonOrchestrator", FakeOrchestrator)

    result = await HorizonReportExecutor(storage=SimpleNamespace(data_dir=tmp_path)).execute(request)

    assert [item.title for item in result.items] == ["Compiler release"]
    assert result.markdown == "Compiler release"
