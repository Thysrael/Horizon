"""Safe Telegram HTML rendering and resilient delivery for report results."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Awaitable, Callable

from aiogram import html
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter
from aiogram.types import BufferedInputFile
from aiogram.utils.formatting import Bold, Text, TextLink

from src.infoservice.execution.contracts import ReportExecutionResult
from src.models import ContentItem


MESSAGE_LIMIT = 3800
DOCUMENT_THRESHOLD = 20
_METADATA_VALUE_LIMIT = 512


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

    def __init__(self, *, today: Callable[[], date] | None = None) -> None:
        self._today = today or (lambda: datetime.now(timezone.utc).date())

    def render(self, result: ReportExecutionResult, report_name: str) -> RenderedReport:
        header = self._overview_header(result, report_name)
        messages = self._pack([header, *[self._item_blocks(item) for item in result.items]])
        if len(messages) <= DOCUMENT_THRESHOLD:
            return RenderedReport(messages=messages)

        report_date = self._report_date(result.markdown)
        document = BufferedInputFile(
            result.markdown.encode("utf-8"), filename=f"report-{report_date}.md"
        )
        return RenderedReport(messages=[self._overview(header, result.items)], document=document)

    @staticmethod
    def _header_markup(value: str) -> str:
        return Text(Bold(value)).as_html()

    def _overview_header(self, result: ReportExecutionResult, report_name: str) -> str:
        """Build the first Telegram message's factual overview before items.

        Metadata is deliberately rendered before item blocks and its size gets
        priority over an exceptionally long report title: partial delivery must
        never look like a complete report.
        """
        details = self._presentation_details(result)
        if not details:
            return self._bounded_markup(report_name, self._header_markup, MESSAGE_LIMIT)
        header_limit = max(0, MESSAGE_LIMIT - len(details) - 1)
        header = self._bounded_markup(report_name, self._header_markup, header_limit)
        return f"{header}\n{details}"

    @classmethod
    def _presentation_details(cls, result: ReportExecutionResult) -> str:
        if result.presentation_period is None or result.presentation_items_selected is None:
            return ""
        period = cls._bounded_escaped(result.presentation_period, _METADATA_VALUE_LIMIT)
        items_seen = cls._bounded_escaped(str(result.all_items_count), _METADATA_VALUE_LIMIT)
        items_selected = cls._bounded_escaped(str(result.presentation_items_selected), _METADATA_VALUE_LIMIT)
        lines = [
            f"Period: {period}",
            f"Items seen: {items_seen}",
            f"Items selected: {items_selected}",
        ]
        if result.failed_sources:
            warning = "⚠️ Partial report — failed sources: "
            base = "\n".join(lines)
            # Reserve a syntactically valid (possibly empty) bold title and
            # the separating newline; arbitrary source labels cannot make the
            # first delivery exceed Telegram's hard limit.
            # There are two newlines in the final header: one after the
            # (possibly empty) title and one before this warning line.
            source_limit = max(0, MESSAGE_LIMIT - len(base) - len(warning) - len("<b></b>") - 2)
            source_names = cls._bounded_escaped(", ".join(result.failed_sources), source_limit)
            lines.append(f"{warning}{source_names}")
        return "\n".join(lines)

    @classmethod
    def _bounded_escaped(cls, value: object, limit: int) -> str:
        """Escape arbitrary metadata while retaining a valid, hard byte budget."""
        raw = str(value)
        split_at = cls._escaped_prefix_length(raw, max(0, limit))
        escaped = html.quote(raw[:split_at])
        if split_at < len(raw) and len(escaped) < limit:
            escaped += "…"
        return escaped

    def _report_date(self, markdown: str) -> str:
        match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", markdown)
        return match.group(0) if match else self._today().isoformat()

    @staticmethod
    def _bounded_markup(value: str, markup: Callable[[str], str], limit: int) -> str:
        """Fit raw text before escaping it, so entities and tags stay complete."""
        if len(markup(value)) <= limit:
            return markup(value)

        lo, hi = 0, len(value)
        while lo < hi:
            midpoint = (lo + hi + 1) // 2
            if len(markup(value[:midpoint])) <= limit:
                lo = midpoint
            else:
                hi = midpoint - 1
        return markup(value[:lo])

    @staticmethod
    def _escaped_prefix_length(value: str, limit: int) -> int:
        """Return the largest raw-text prefix whose escaped form fits ``limit``."""
        used = 0
        for index, character in enumerate(value):
            encoded_length = len(html.quote(character))
            if used + encoded_length > limit:
                return index
            used += encoded_length
        return len(value)

    @staticmethod
    def _title_markup(item: ContentItem, title: str) -> str:
        return Text(TextLink(Bold(title), url=str(item.url))).as_html()

    def _overview(self, header: str, items: list[ContentItem]) -> str:
        """Keep the first item in the fallback message, not just its title."""
        if not items:
            return header

        item_limit = MESSAGE_LIMIT - len(header) - 2
        # A near-limit report name leaves no space for an HTML link plus a
        # summary character. The bounded header is still a valid overview;
        # the attached Markdown remains the complete report.
        minimum_item_markup = len(self._title_markup(items[0], "")) + 1
        if item_limit < minimum_item_markup:
            return header
        try:
            first_block = self._item_blocks(items[0], limit=item_limit)[0]
        except ValueError:
            # Some tight budgets can represent a linked title but not the
            # separator plus the first escaped summary character. In that
            # case the bounded header is the only valid overview.
            return header
        return f"{header}\n\n{first_block}"

    def _item_blocks(self, item: ContentItem, *, limit: int = MESSAGE_LIMIT) -> list[str]:
        title_markup = lambda value: self._title_markup(item, value)
        title = self._bounded_markup(item.title, title_markup, limit)
        paragraphs = (item.ai_summary or item.content or "").split("\n\n")
        if not any(paragraph.strip() for paragraph in paragraphs):
            return [title]

        # Leave room for a separator and the largest Telegram HTML entity (&quot;).
        body_title = self._bounded_markup(item.title, title_markup, limit - 8)
        prefix = f"{body_title}\n\n"
        body_limit = limit - len(prefix)
        blocks: list[str] = []
        for paragraph in paragraphs:
            raw_paragraph = paragraph.strip()
            if not raw_paragraph:
                continue
            while raw_paragraph:
                split_at = self._escaped_prefix_length(raw_paragraph, body_limit)
                # ``body_limit`` is at least six when the title is representable;
                # still guard this invariant to make a malformed input unable to loop.
                if split_at == 0:
                    blocks.append(title)
                    body_title = self._bounded_markup(item.title, title_markup, limit - 8)
                    prefix = f"{body_title}\n\n"
                    body_limit = limit - len(prefix)
                    if body_limit < len(html.quote(raw_paragraph[0])):
                        raise ValueError("Telegram item link leaves no room for content")
                    continue
                blocks.append(f"{prefix}{html.quote(raw_paragraph[:split_at])}")
                raw_paragraph = raw_paragraph[split_at:]
        return blocks

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
