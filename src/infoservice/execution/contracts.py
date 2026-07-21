"""Side-effect-free report execution data transfer objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.models import ContentItem


@dataclass(frozen=True, slots=True)
class ReportExecutionRequest:
    report_id: UUID
    config: Any
    api_key: str
    custom_instruction: str | None = None
    lookback_hours: int | None = None
    model: str | None = None


@dataclass(frozen=True, slots=True)
class ReportExecutionResult:
    markdown: str
    items: list[ContentItem]
    all_items_count: int
    fetch_report: Any
    usage: Any
    # Presentation-only context is attached by the durable execution layer.
    # Keeping it on the immutable result lets renderers retain their small,
    # two-argument interface while still making partial collection explicit.
    presentation_period: str | None = None
    presentation_items_selected: int | None = None
    failed_sources: tuple[str, ...] = ()
