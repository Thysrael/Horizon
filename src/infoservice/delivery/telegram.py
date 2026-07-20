"""Safe Telegram HTML rendering and resilient delivery for report results."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from aiogram import html
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter
from aiogram.types import BufferedInputFile
from aiogram.utils.formatting import Bold, Text, TextLink

from src.infoservice.execution.contracts import ReportExecutionResult
from src.models import ContentItem


MESSAGE_LIMIT = 3800
DOCUMENT_THRESHOLD = 20


@dataclass(frozen=True, slots=True)
class RenderedReport:
    messages: list[str]
    document: BufferedInputFile | None = None


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    status: str
    detail: str | None = None


class TelegramReportRenderer:
    """Render report data into Telegram's limited HTML message format."""

    def render(self, result: ReportExecutionResult, report_name: str) -> RenderedReport:
        header = Text(Bold(report_name)).as_html()
        messages = self._pack([header, *[self._item_blocks(item) for item in result.items]])
        if len(messages) <= DOCUMENT_THRESHOLD:
            return RenderedReport(messages=messages)

        report_date = self._report_date(result.markdown)
        document = BufferedInputFile(
            result.markdown.encode("utf-8"), filename=f"report-{report_date}.md"
        )
        return RenderedReport(messages=[self._truncate(header)], document=document)

    @staticmethod
    def _report_date(markdown: str) -> str:
        match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", markdown)
        return match.group(0) if match else datetime.now(timezone.utc).date().isoformat()

    @staticmethod
    def _truncate(value: str) -> str:
        return value[:MESSAGE_LIMIT]

    def _item_blocks(self, item: ContentItem) -> list[str]:
        title = Text(TextLink(Bold(item.title), url=str(item.url))).as_html()
        paragraphs = (item.ai_summary or item.content or "").split("\n\n")
        if not any(paragraph.strip() for paragraph in paragraphs):
            return [title]

        blocks: list[str] = []
        current = title
        for paragraph in paragraphs:
            escaped = html.quote(paragraph.strip())
            if not escaped:
                continue
            candidate = f"{current}\n\n{escaped}"
            if len(candidate) <= MESSAGE_LIMIT:
                current = candidate
                continue
            blocks.append(current)
            current = title
            for part in self._split_paragraph(escaped, MESSAGE_LIMIT - len(title) - 2):
                candidate = f"{title}\n\n{part}"
                if len(candidate) > MESSAGE_LIMIT:
                    blocks.append(self._truncate(candidate))
                else:
                    blocks.append(candidate)
            current = title
        if current != title or not blocks:
            blocks.append(current)
        return blocks

    @staticmethod
    def _split_paragraph(paragraph: str, limit: int) -> list[str]:
        if len(paragraph) <= limit:
            return [paragraph]
        parts: list[str] = []
        remaining = paragraph
        while len(remaining) > limit:
            split_at = remaining.rfind(" ", 0, limit + 1)
            if split_at <= 0:
                split_at = limit
            parts.append(remaining[:split_at].rstrip())
            remaining = remaining[split_at:].lstrip()
        if remaining:
            parts.append(remaining)
        return parts

    @staticmethod
    def _pack(groups: list[str | list[str]]) -> list[str]:
        messages: list[str] = []
        current = ""
        for group in groups:
            blocks = [group] if isinstance(group, str) else group
            for block in blocks:
                candidate = block if not current else f"{current}\n\n{block}"
                if current and len(candidate) > MESSAGE_LIMIT:
                    messages.append(current)
                    current = block
                else:
                    current = candidate
        if current:
            messages.append(current)
        return messages


class TelegramDelivery:
    """Send rendered reports with Telegram-aware retry handling."""

    def __init__(
        self,
        bot: object,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._bot = bot
        self._sleep = sleep

    async def send(self, chat_id: int, rendered: RenderedReport) -> DeliveryResult:
        try:
            for message in rendered.messages:
                await self._send_with_retries(self._bot.send_message, chat_id, text=message, parse_mode="HTML")
            if rendered.document is not None:
                await self._send_with_retries(self._bot.send_document, chat_id, document=rendered.document)
        except TelegramForbiddenError:
            return DeliveryResult(status="forbidden")
        except Exception:
            return DeliveryResult(status="failed")
        return DeliveryResult(status="sent")

    async def _send_with_retries(self, method: Callable[..., Awaitable[object]], chat_id: int, **kwargs: object) -> None:
        for attempt in range(3):
            try:
                await method(chat_id, **kwargs)
                return
            except TelegramForbiddenError:
                raise
            except TelegramRetryAfter as error:
                if attempt == 2:
                    raise
                await self._sleep(error.retry_after)
            except TelegramNetworkError:
                if attempt == 2:
                    raise
                await self._sleep(2**attempt)
