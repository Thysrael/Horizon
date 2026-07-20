from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter

from src.infoservice.delivery.telegram import TelegramDelivery, TelegramReportRenderer
from src.infoservice.execution.contracts import ReportExecutionResult
from src.models import ContentItem, SourceType


def _item(index: int, *, title: str = "Item", summary: str = "Summary") -> ContentItem:
    return ContentItem(
        id=f"rss:item-{index}",
        source_type=SourceType.RSS,
        title=title,
        url=f"https://example.com/items/{index}",
        published_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
        ai_summary=summary,
    )


def _result(*items: ContentItem, markdown: str = "# Report") -> ReportExecutionResult:
    return ReportExecutionResult(
        markdown=markdown,
        items=list(items),
        all_items_count=len(items),
        fetch_report={},
        usage={},
    )


@pytest.fixture
def renderer() -> TelegramReportRenderer:
    return TelegramReportRenderer()


def test_renderer_escapes_and_chunks_on_item_boundaries(renderer: TelegramReportRenderer) -> None:
    result = _result(
        *[_item(index, title=f"Item <{index}>", summary="Details " * 400) for index in range(1, 5)]
    )

    rendered = renderer.render(result, "AI <daily>")

    assert all(len(part) <= 3800 for part in rendered.messages)
    assert "&lt;daily&gt;" in rendered.messages[0]
    assert "<1>" not in "".join(rendered.messages)
    assert all("https://example.com/items/" in part for part in rendered.messages[1:])


def test_renderer_splits_an_oversized_item_at_paragraph_boundaries(renderer: TelegramReportRenderer) -> None:
    result = _result(_item(1, summary=("First paragraph.\n\n" + "Second paragraph.\n\n") * 250))

    rendered = renderer.render(result, "Daily")

    assert len(rendered.messages) > 1
    assert all(len(part) <= 3800 for part in rendered.messages)
    assert all("https://example.com/items/1" in part for part in rendered.messages[1:])


def test_renderer_uses_markdown_document_after_twenty_messages(renderer: TelegramReportRenderer) -> None:
    result = _result(*[_item(index, summary="Details " * 500) for index in range(1, 22)], markdown="# Full report")

    rendered = renderer.render(result, "Daily")

    assert len(rendered.messages) == 1
    assert rendered.document is not None
    assert rendered.document.filename == "report-2026-07-20.md"
    assert rendered.document.data == b"# Full report"


@pytest.mark.asyncio
async def test_429_uses_retry_after() -> None:
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=[
        TelegramRetryAfter(method=None, message="rate", retry_after=2),
        object(),
    ]))
    sleep = AsyncMock()
    delivery = TelegramDelivery(bot, sleep=sleep)
    rendered = TelegramReportRenderer().render(_result(_item(1)), "Daily")

    assert (await delivery.send(42, rendered)).status == "sent"
    sleep.assert_awaited_once_with(2)
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_transient_failures_retry_with_exponential_delays() -> None:
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=[
        TelegramNetworkError(method=None, message="offline"),
        TelegramNetworkError(method=None, message="offline"),
        object(),
    ]))
    sleep = AsyncMock()
    delivery = TelegramDelivery(bot, sleep=sleep)
    rendered = TelegramReportRenderer().render(_result(_item(1)), "Daily")

    assert (await delivery.send(42, rendered)).status == "sent"
    assert [call.args[0] for call in sleep.await_args_list] == [1, 2]


@pytest.mark.asyncio
async def test_forbidden_chat_returns_permanent_safe_status() -> None:
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=TelegramForbiddenError(method=None, message="blocked")))
    delivery = TelegramDelivery(bot, sleep=AsyncMock())
    rendered = TelegramReportRenderer().render(_result(_item(1)), "Daily")

    result = await delivery.send(42, rendered)

    assert result.status == "forbidden"
    assert result.detail is None
