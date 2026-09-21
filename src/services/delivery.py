"""Delivery message builders shared by chat-style notification channels.

Webhook and WeChat delivery both split one language's briefing into a list of
messages (one full summary, or an overview plus one message per item). The
transports differ; this module holds only the channel-neutral splitting logic.
"""

from datetime import datetime, timezone
from typing import Any, List

from ..ai.summarizer import DailySummarizer
from ..models import (
    ClassificationResult,
    ContentAnalysis,
    ContentArtifact,
    ContentBlock,
    ContentItem,
    ProcessingResult,
    SourceType,
)


def build_base_variables(
    *, date: str, lang: str, important_count: int, all_items_count: int
) -> dict[str, Any]:
    """Build the template variables shared by every delivery message."""
    return {
        "date": date,
        "language": lang,
        "important_items": important_count,
        "all_items": all_items_count,
        "result": "success",
        "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
    }


def build_overview_and_items(
    summarizer: DailySummarizer,
    important_items: List[ContentItem],
    all_items_count: int,
    date: str,
    lang: str,
) -> tuple[str, List[str]]:
    """Render the overview message and one message per selected item."""
    overview = summarizer.generate_webhook_overview(
        important_items, date, all_items_count, language=lang
    )
    view = summarizer.build_view(important_items, lang)
    items = [
        summarizer.generate_webhook_item(
            view_item.item,
            language=lang,
            index=view_item.index,
            total=view_item.group_count,
            title=view_item.title,
            score=view_item.score,
        )
        for group in view.groups
        for view_item in group.items
    ]
    return overview, items


def build_delivery_messages(
    *,
    delivery: str,
    overview_position: str,
    base_vars: dict[str, Any],
    summary: str,
    important_items: List[ContentItem],
    all_items_count: int,
    date: str,
    lang: str,
    summarizer: DailySummarizer,
) -> List[dict[str, Any]]:
    """Build templated delivery messages for one language.

    ``delivery`` selects one full ``summary`` message, or ``summary_and_items``:
    an overview plus one message per selected item, with ``overview_position``
    controlling the order. Each message carries the template variables that
    webhook bodies can reference.
    """
    if delivery == "summary_and_items":
        overview, item_texts = build_overview_and_items(
            summarizer, important_items, all_items_count, date, lang
        )
        overview_message = {
            **base_vars,
            "message_title": (
                f"Horizon {date} 总览" if lang == "zh" else f"Horizon {date} Overview"
            ),
            "message_kind": "overview",
            "summary": overview,
        }
        view = summarizer.build_view(important_items, lang)
        view_items = [(group, view_item) for group in view.groups for view_item in group.items]
        item_messages = [
            {
                **base_vars,
                "message_title": (
                    f"{group.name} {view_item.index}/{view_item.group_count} {view_item.title}"
                ),
                "message_kind": "item",
                "item_index": view_item.global_index,
                "item_count": view.item_count,
                "profile_item_index": view_item.index,
                "profile_item_count": view_item.group_count,
                "item_profile": group.profile_id,
                "item_profile_name": group.name,
                "item_title": view_item.title,
                "item_url": str(view_item.item.url),
                "item_score": view_item.score if view_item.score != "?" else "",
                "summary": item_text,
            }
            for (group, view_item), item_text in zip(view_items, item_texts)
        ]

        if overview_position == "last":
            return list(reversed(item_messages)) + [overview_message]
        return [overview_message] + item_messages

    return [
        {
            **base_vars,
            "message_title": (
                f"Horizon {date} 日报" if lang == "zh" else f"Horizon {date} Daily"
            ),
            "message_kind": "summary",
            "summary": summary,
        }
    ]


# ── sample data for the `horizon-webhook` / `horizon-wechat` test commands ──


def _sample_processing(
    score: float, summary: str, tags: list[str], title_zh: str, summary_zh: str
) -> ProcessingResult:
    return ProcessingResult(
        classification=ClassificationResult(profile="tech-news", method="source_override"),
        analysis=ContentAnalysis(score=score, reason="Sample item", summary=summary, tags=tags),
        artifacts={
            "zh": ContentArtifact(
                language="zh",
                title=title_zh,
                blocks=[ContentBlock(id="summary", title="摘要", content=summary_zh, primary=True)],
            )
        },
    )


def make_sample_items() -> List[ContentItem]:
    """Two fixed items used to preview or test a delivery channel."""
    return [
        ContentItem(
            id="github:test:1",
            source_type=SourceType.GITHUB,
            title="GPT-5 Released with Multimodal Capabilities",
            url="https://example.com/gpt5",
            content="OpenAI announced GPT-5 with major improvements.",
            author="openai",
            published_at=datetime(2026, 4, 24, 10, 0, tzinfo=timezone.utc),
            fetched_at=datetime(2026, 4, 24, 12, 0, tzinfo=timezone.utc),
            profile="tech-news",
            processing=_sample_processing(
                score=9.0,
                summary="OpenAI released GPT-5 featuring multimodal capabilities and improved reasoning.",
                tags=["ai", "llm", "openai"],
                title_zh="GPT-5 发布：多模态能力大幅提升",
                summary_zh="OpenAI 发布了 GPT-5，具备多模态能力和更强的推理能力。",
            ),
        ),
        ContentItem(
            id="hackernews:test:2",
            source_type=SourceType.HACKERNEWS,
            title="New Linux Kernel 7.0 Released",
            url="https://example.com/linux7",
            content="Linux kernel 7.0 brings significant performance improvements.",
            author="torvalds",
            published_at=datetime(2026, 4, 24, 8, 0, tzinfo=timezone.utc),
            fetched_at=datetime(2026, 4, 24, 12, 0, tzinfo=timezone.utc),
            profile="tech-news",
            processing=_sample_processing(
                score=7.5,
                summary="Linux kernel 7.0 released with performance gains and new hardware support.",
                tags=["linux", "kernel", "performance"],
                title_zh="Linux 内核 7.0 发布",
                summary_zh="Linux 内核 7.0 发布，带来显著性能提升和新硬件支持。",
            ),
        ),
    ]


async def sample_briefing(lang: str) -> tuple[str, List[ContentItem], DailySummarizer, str]:
    """``(today, items, summarizer, summary)`` for a channel test run."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    items = make_sample_items()
    summarizer = DailySummarizer()
    summary = await summarizer.generate_summary(items, today, len(items), language=lang)
    return today, items, summarizer, summary
