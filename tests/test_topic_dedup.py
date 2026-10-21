import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

from rich.console import Console

import src.orchestrator as orchestrator_module
from src.models import (
    ClassificationResult,
    ContentAnalysis,
    ContentItem,
    ProcessingResult,
    SourceType,
)
from src.orchestrator import HorizonOrchestrator
from src.processing.content import COMMENTS_MARKER, split_content


def make_item(
    item_id: str,
    score: float,
    *,
    content: str | None = None,
    source_type: SourceType = SourceType.RSS,
) -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=source_type,
        title=f"title {item_id}",
        url=f"https://example.com/{item_id}",
        content=content,
        published_at=datetime.now(timezone.utc),
        profile="tech-news",
        processing=ProcessingResult(
            classification=ClassificationResult(
                profile="tech-news", method="source_override"
            ),
            analysis=ContentAnalysis(score=score, reason="test", summary=item_id),
        ),
    )


class FakeClient:
    def __init__(self, response: dict) -> None:
        self.response = response

    async def complete(self, **kwargs):  # type: ignore[no-untyped-def]
        return json.dumps(self.response)


def run_dedup(monkeypatch, items, response):  # type: ignore[no-untyped-def]
    client = FakeClient(response)
    monkeypatch.setattr(orchestrator_module, "create_ai_client", lambda config: client)
    orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(ai=None)
    orchestrator.console = Console(record=True)
    return asyncio.run(orchestrator.merge_topic_duplicates(items, log=False))


def test_primary_is_highest_score_regardless_of_model_order(monkeypatch) -> None:
    items = [make_item("high", 9.0), make_item("low", 8.0)]
    result = run_dedup(monkeypatch, items, {"duplicates": [[1, 0]]})

    assert [item.id for item in result] == ["high"]


def test_invalid_indices_are_ignored(monkeypatch) -> None:
    items = [make_item(str(i), 9.0 - i) for i in range(3)]
    response = {"duplicates": [[True, 2], [2, 99], ["1", 2], "x", [1]]}
    result = run_dedup(monkeypatch, items, response)

    assert [item.id for item in result] == ["0", "1", "2"]


def test_overlapping_groups_are_merged_into_one_topic(monkeypatch) -> None:
    items = [
        make_item(str(i), 9.0 - i, content=f"article {i}") for i in range(4)
    ]
    response = {"duplicates": [[0, 1], [0, 2]]}
    result = run_dedup(monkeypatch, items, response)

    assert [item.id for item in result] == ["0", "3"]
    assert "article 1" in result[0].content and "article 2" in result[0].content


def test_duplicate_source_text_is_merged_before_primary_comments(monkeypatch) -> None:
    primary = make_item(
        "hn",
        9.0,
        content=f"story text\n{COMMENTS_MARKER}\ncomment one",
        source_type=SourceType.HACKERNEWS,
    )
    dup = make_item("rss", 8.0, content="full article text")
    result = run_dedup(monkeypatch, [primary, dup], {"duplicates": [[0, 1]]})

    parts = split_content(result[0].content)
    assert "full article text" in parts.main
    assert parts.comments == "comment one"


def test_duplicate_comments_stay_comments(monkeypatch) -> None:
    primary = make_item("rss", 9.0, content="article text")
    dup = make_item(
        "hn",
        8.0,
        content=f"story text\n{COMMENTS_MARKER}\ncomment two",
        source_type=SourceType.HACKERNEWS,
    )
    result = run_dedup(monkeypatch, [primary, dup], {"duplicates": [[0, 1]]})

    parts = split_content(result[0].content)
    assert "article text" in parts.main and "story text" in parts.main
    assert parts.comments == "--- From hackernews ---\ncomment two"


def test_comment_only_duplicate_keeps_source_label(monkeypatch) -> None:
    primary = make_item("rss", 9.0, content="article")
    dup = make_item(
        "hn",
        8.0,
        content=f"{COMMENTS_MARKER}\n[reader]: useful comment",
        source_type=SourceType.HACKERNEWS,
    )
    result = run_dedup(monkeypatch, [primary, dup], {"duplicates": [[0, 1]]})

    parts = split_content(result[0].content)
    assert parts.main == "article"
    assert parts.comments == "--- From hackernews ---\n[reader]: useful comment"
