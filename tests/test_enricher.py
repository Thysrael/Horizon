import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.ai.enricher import ContentEnricher
from src.models import (
    ClassificationResult,
    ContentAnalysis,
    ContentArtifact,
    ContentBlock,
    ContentItem,
    ProcessingResult,
    SourceType,
)
from src.processing import ProfileRegistry
from src.processing.tools import ToolRegistry, ToolResult


PROFILES = ProfileRegistry.load(
    Path(__file__).resolve().parents[1] / "profiles", "tech-news"
)


def make_item() -> ContentItem:
    return ContentItem(
        id="rss:test:item",
        source_type=SourceType.RSS,
        title="A technical release",
        url="https://example.com/item",
        content="A project released a new architecture.",
        published_at=datetime.now(timezone.utc),
        profile="tech-news",
        processing=ProcessingResult(
            classification=ClassificationResult(
                profile="tech-news", method="source_override"
            ),
            analysis=ContentAnalysis(
                score=8.5,
                reason="Important release",
                summary="A new architecture was released.",
                tags=["systems"],
            ),
        ),
    )


class FakeTools:
    names = {"web_search", "history_search"}

    async def execute(self, request_id, block_id, tool, arguments, current_item=None):
        assert block_id == "background"
        assert tool == "web_search"
        assert arguments == {"query": "project architecture"}
        return ToolResult(
            request_id=request_id,
            block_id=block_id,
            tool=tool,
            results=[
                {
                    "title": "Project documentation",
                    "url": "https://docs.example.com/project",
                    "text": "Architecture background.",
                }
            ],
        )


def test_enrichment_generates_blocks_and_validated_sources():
    responses = iter(
        [
            json.dumps(
                {
                    "tool_requests": [
                        {
                            "block_id": "background",
                            "tool": "web_search",
                            "arguments": {"query": "project architecture"},
                            "purpose": "Explain the existing architecture",
                        }
                    ]
                }
            ),
            json.dumps(
                {
                    "title": "新架構發佈",
                    "blocks": [
                        {
                            "id": "summary",
                            "title": "摘要",
                            "content": "項目發佈了新的架構，它改變了系統設計，並採用了新的邊界。",
                            "source_refs": [],
                        }
                    ],
                }
            ),
            json.dumps(
                {
                    "title": "新架構發佈",
                    "blocks": [
                        {
                            "id": "summary",
                            "type": "section",
                            "title": "摘要",
                            "content": "项目发布了新的架构，它改变了系统设计，并采用了新的边界。",
                            "source_refs": [],
                        },
                        {
                            "id": "background",
                            "type": "section",
                            "title": "未隔离的背景",
                            "content": "这个版本应被丢弃。",
                            "source_refs": [],
                        },
                    ],
                }
            ),
            json.dumps(
                {
                    "title": "",
                    "block": {
                        "id": "background",
                        "type": "section",
                        "title": "背景",
                        "content": "旧架构的背景信息。",
                        "source_refs": ["tool-1"],
                    },
                }
            ),
        ]
    )
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return next(responses)

    item = make_item()
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["zh"],
        tools=FakeTools(),
    )
    asyncio.run(enricher._enrich_item(item))

    artifact = item.processing.artifacts["zh"]
    assert artifact.title == "新架构发布"
    assert artifact.blocks[0].content == "项目发布了新的架构，它改变了系统设计，并采用了新的边界。"
    assert [block.id for block in artifact.blocks] == [
        "summary",
        "background",
    ]
    assert artifact.blocks[-1].title == "背景"
    assert artifact.blocks[0].primary is True
    assert artifact.blocks[1].primary is False
    assert artifact.blocks[-1].source_refs == ["tool-1-1"]
    assert artifact.sources[0].url == "https://docs.example.com/project"
    assert len(requests) == 4
    assert "explicitly mentioned in the item" in requests[0]["system"]
    assert "Treat the source item as the primary account" in requests[1]["system"]
    assert "Simplified Chinese (language tag `zh`)" in requests[1]["system"]
    assert "Treat the source item as the primary account" in requests[3]["system"]
    assert "https://docs.example.com/project" not in requests[1]["user"]
    assert "https://docs.example.com/project" in requests[3]["user"]


def test_enrichment_rejects_tool_on_unapproved_block():
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return json.dumps(
            {
                "tool_requests": [
                    {
                        "block_id": "summary",
                        "tool": "web_search",
                        "arguments": {"query": "unapproved"},
                        "purpose": "Rewrite the news",
                    }
                ]
            }
        )

    tools = SimpleNamespace(names=FakeTools.names, execute=AsyncMock())
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["zh"],
        tools=tools,
    )

    with pytest.raises(ValueError, match="Invalid enrichment tool plan") as exc_info:
        asyncio.run(enricher._enrich_item(make_item()))

    assert "not allowed for block summary" in str(exc_info.value.__cause__)
    assert len(requests) == 2
    assert "not allowed for block summary" in requests[1]["user"]
    tools.execute.assert_not_awaited()


@pytest.mark.parametrize("block_id,error", [
    ("summary", "Tool web_search is not allowed for block summary"),
    ("unknown", "Tool request targets unknown block: unknown"),
])
def test_enrichment_repairs_tool_permissions_before_executing(block_id, error):
    allowed_request = {
        "block_id": "background",
        "tool": "web_search",
        "arguments": {"query": "project architecture"},
        "purpose": "Explain the existing architecture",
    }
    complete = AsyncMock(side_effect=[
        json.dumps({"tool_requests": [
            allowed_request,
            {**allowed_request, "block_id": block_id},
        ]}),
        json.dumps({"tool_requests": [allowed_request]}),
    ])
    tools = FakeTools()
    tools.execute = AsyncMock(wraps=tools.execute)
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete), PROFILES, ["zh"], tools=tools,
    )

    results = asyncio.run(enricher._plan_and_execute_tools(make_item(), PROFILES.get("tech-news")))

    assert complete.await_count == 2
    assert error in complete.await_args_list[1].kwargs["user"]
    # An invalid plan must not execute even its allowed requests before correction.
    tools.execute.assert_awaited_once()
    assert len(results) == 1
    assert results[0].block_id == "background"


def test_enrichment_rejects_malformed_tool_plan():
    async def complete(**kwargs):
        return "[]"

    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["zh"],
        tools=FakeTools(),
    )

    with pytest.raises(ValueError, match="tool plan"):
        asyncio.run(enricher._enrich_item(make_item()))


def test_enrichment_repairs_malformed_tool_plan_once():
    responses = iter(
        [
            "[]",
            json.dumps({"tool_requests": []}),
            json.dumps(
                {
                    "title": "Technical release",
                    "blocks": [
                        {
                            "id": "summary",
                            "type": "section",
                            "title": "Summary",
                            "content": "A complete summary.",
                            "source_refs": [],
                        },
                        {
                            "id": "background",
                            "type": "section",
                            "title": "Background",
                            "content": "Context for the release.",
                            "source_refs": [],
                        }
                    ],
                }
            ),
        ]
    )
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return next(responses)

    item = make_item()
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["en"],
        tools=FakeTools(),
    )

    asyncio.run(enricher._enrich_item(item))

    assert len(requests) == 3
    assert all(request["temperature"] == 0 for request in requests)
    assert requests[1]["temperature"] == 0
    assert item.processing.artifacts["en"].blocks[0].id == "summary"


def test_enrichment_repairs_empty_blog_block_once():
    responses = iter(
        [
            json.dumps(
                {
                    "title": "A technical story",
                    "blocks": [
                        {
                            "id": "background",
                            "title": " ",
                            "content": "",
                            "source_refs": [],
                        },
                        {
                            "id": "solution",
                            "title": "Solution and results",
                            "content": "The author explains the implementation.",
                            "source_refs": [],
                        },
                        {
                            "id": "takeaway",
                            "title": "Takeaway",
                            "content": "The approach is useful in bounded cases.",
                            "source_refs": [],
                        }
                    ],
                }
            ),
            json.dumps(
                {
                    "title": "A technical story",
                    "blocks": [
                        {
                            "id": "background",
                            "title": "Background",
                            "content": "The author frames the original problem and constraints.",
                            "source_refs": [],
                        },
                        {
                            "id": "solution",
                            "title": "Solution and results",
                            "content": "The author explains the implementation and its effects.",
                            "source_refs": [],
                        },
                        {
                            "id": "takeaway",
                            "title": "Takeaway",
                            "content": "The approach is useful in bounded cases.",
                            "source_refs": [],
                        }
                    ],
                }
            ),
        ]
    )
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return next(responses)

    item = make_item()
    item.profile = "tech-blog"
    item.processing.classification.profile = "tech-blog"
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["en"],
        tools=FakeTools(),
    )

    asyncio.run(enricher._enrich_item(item))

    assert len(requests) == 2
    assert requests[1]["temperature"] == 0
    assert "corrected JSON object" in requests[1]["user"]
    assert [
        block.id for block in item.processing.artifacts["en"].blocks
    ] == ["background", "solution", "takeaway"]
    assert all(
        not block.primary for block in item.processing.artifacts["en"].blocks
    )


def test_enrichment_repairs_schema_type_used_as_blog_block_id():
    responses = iter(
        [
            json.dumps(
                {
                    "title": "A technical story",
                    "blocks": [
                        {
                            "id": "section",
                            "type": "section",
                            "title": "Background",
                            "content": "A complete but misidentified background block.",
                            "source_refs": [],
                        },
                        {
                            "id": "solution",
                            "title": "Solution and results",
                            "content": "The implementation produced a measured result.",
                            "source_refs": [],
                        },
                        {
                            "id": "takeaway",
                            "title": "Takeaway",
                            "content": "The method has a clear bounded use.",
                            "source_refs": [],
                        }
                    ],
                }
            ),
            json.dumps(
                {
                    "title": "A technical story",
                    "blocks": [
                        {
                            "id": "background",
                            "title": "Background",
                            "content": "The corrected background and constraints.",
                            "source_refs": [],
                        },
                        {
                            "id": "solution",
                            "title": "Solution and results",
                            "content": "The implementation produced a measured result.",
                            "source_refs": [],
                        },
                        {
                            "id": "takeaway",
                            "title": "Takeaway",
                            "content": "The method has a clear bounded use.",
                            "source_refs": [],
                        }
                    ],
                }
            ),
        ]
    )
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        return next(responses)

    item = make_item()
    item.profile = "tech-blog"
    item.processing.classification.profile = "tech-blog"
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["en"],
        tools=FakeTools(),
    )

    asyncio.run(enricher._enrich_item(item))

    assert len(requests) == 2
    assert "unknown blocks: section" in requests[1]["user"]
    assert item.processing.artifacts["en"].blocks[0].id == "background"


def test_failed_reenrichment_removes_stale_target_artifact():
    async def complete(**kwargs):
        return json.dumps(
            {
                "title": "A technical story",
                "blocks": [
                    {
                        "id": "story",
                        "type": "section",
                        "title": "",
                        "content": "",
                        "source_refs": [],
                    }
                ],
            }
        )

    item = make_item()
    item.profile = "tech-blog"
    item.processing.classification.profile = "tech-blog"
    item.processing.artifacts["en"] = ContentArtifact(
        language="en",
        title="Stale story",
    )
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["en"],
        tools=FakeTools(),
    )

    with pytest.raises(ValueError, match="Invalid enrichment artifact"):
        asyncio.run(enricher._enrich_item(item))

    assert "en" not in item.processing.artifacts


def test_enrichment_rejects_cross_block_source_reference():
    block = ContentBlock(
        id="summary",
        type="section",
        title="News",
        content="Content",
        source_refs=["tool-1-1"],
    )
    tool_result = ToolResult(
        request_id="tool-1",
        block_id="background",
        tool="web_search",
        results=[
            {
                "title": "Source",
                "url": "https://example.com/source",
                "text": "Context",
            }
        ],
    )

    with pytest.raises(ValueError, match="unknown source refs"):
        ContentEnricher._validate_blocks(
            [block], PROFILES.get("tech-news"), [tool_result]
        )


def test_enrichment_rejects_empty_required_block():
    block = ContentBlock(
        id="summary",
        type="section",
        title=" ",
        content="",
        source_refs=[],
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        ContentEnricher._validate_blocks(
            [block], PROFILES.get("tech-news"), []
        )


def test_enrichment_batch_reports_failure_without_discarding_successes():
    async def complete(**kwargs):
        raise RuntimeError("AI unavailable")

    successful_item = make_item()
    failed_item = make_item().model_copy(update={"id": "rss:test:failed"})
    enricher = ContentEnricher(
        SimpleNamespace(complete=complete),
        PROFILES,
        ["zh"],
        tools=FakeTools(),
    )

    async def enrich_item(item):  # type: ignore[no-untyped-def]
        if item.id == failed_item.id:
            raise RuntimeError("AI unavailable")

    enricher._enrich_item = enrich_item  # type: ignore[method-assign]

    result = asyncio.run(enricher.enrich_batch([successful_item, failed_item]))

    assert result.status == "partial_failure"
    assert result.succeeded_ids == [successful_item.id]
    assert result.failed_ids == [failed_item.id]
    assert result.failures[failed_item.id] == "RuntimeError: AI unavailable"


def test_history_search_reuses_one_call_for_both_languages(tmp_path, monkeypatch):
    (tmp_path / "horizon-2026-04-01-en.md").write_text(
        "### [Atlas preview](https://example.com/preview) ⭐️ 8/10\n\n"
        "Atlas preview requires manual batch configuration.\n\n---\n",
        encoding="utf-8",
    )
    tools = ToolRegistry(tmp_path)
    tool_calls = []
    execute = tools.execute

    async def record_execute(**kwargs):
        tool_calls.append(kwargs)
        return await execute(**kwargs)

    monkeypatch.setattr(tools, "execute", record_execute)
    requests = []

    async def complete(**kwargs):
        requests.append(kwargs)
        if kwargs["system"].startswith("# Tool planning"):
            return json.dumps({"tool_requests": [
                {"block_id": "background", "tool": "history_search",
                 "arguments": {"query": query}, "purpose": "Find the earlier version"}
                for query in ("Atlas preview", "Atlas batch")
            ]})
        if "Generate only block `background`" in kwargs["system"]:
            assert "Atlas preview requires manual batch configuration." in kwargs["user"]
            return json.dumps({"block": {
                "id": "background", "title": "Earlier coverage",
                "content": "The April 1 digest covered the preview's manual batch configuration.",
                "source_refs": ["tool-1-1"],
            }})
        assert "manual batch configuration" not in kwargs["user"]
        return json.dumps({"title": "Atlas release", "blocks": [{
            "id": "summary", "title": "Summary", "content": "Atlas now automates batching.",
        }]})

    item = make_item()
    item.published_at = datetime(2026, 4, 2, tzinfo=timezone.utc)
    enricher = ContentEnricher(SimpleNamespace(complete=complete), PROFILES, ["en", "zh"], tools=tools)

    asyncio.run(enricher._enrich_item(item))

    assert len(tool_calls) == 1
    assert tool_calls[0]["current_item"] is item
    # One existing planning call, then base and background generation per language.
    assert len(requests) == 5
    for language in ("en", "zh"):
        artifact = item.processing.artifacts[language]
        assert artifact.sources[0].url == "https://example.com/preview"
        assert artifact.sources[0].title.startswith("2026-04-01")
        assert artifact.blocks[-1].source_refs == ["tool-1-1"]
