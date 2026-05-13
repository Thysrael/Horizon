"""OpenBB Platform scraper.

Pulls company news (and optionally filings) from the OpenBB SDK and maps
them into ContentItem instances so the rest of the Horizon pipeline
(deduplication, AI scoring, enrichment, summarization) treats them the
same way as RSS or Hacker News items.

The `openbb` package is declared as an optional dependency in
pyproject.toml. If it is not installed the scraper logs a warning and
returns an empty list rather than crashing, so a user can enable the
OpenBB source without blocking the core pipeline.

Design notes:

* One ``news.company()`` call per watchlist. Grouping tickers by provider
  keeps request counts low (the OpenBB multi-symbol form does the
  fan-out internally for providers that support it).
* Filings fetches are optional and off by default; SEC filings are free
  but noisy for non-investors.
* ``obb`` is synchronous, so we wrap calls in ``asyncio.to_thread`` to
  keep the orchestrator's event loop responsive.
* Provider credentials (FMP/Benzinga/Polygon/Intrinio/...) are read by
  the OpenBB SDK from its own settings/environment and are not passed
  through Horizon.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional

import httpx

from .base import BaseScraper
from ..models import ContentItem, OpenBBConfig, OpenBBWatchlist, SourceType

logger = logging.getLogger(__name__)


class OpenBBScraper(BaseScraper):
    """Scraper backed by the OpenBB Platform Python SDK."""

    SOURCE_TYPE = SourceType.OPENBB

    def __init__(self, config: OpenBBConfig, http_client: httpx.AsyncClient):
        """Initialize the scraper.

        Args:
            config: OpenBB source configuration.
            http_client: Shared httpx client (unused here; kept for the
                BaseScraper contract).
        """
        super().__init__({"openbb": config}, http_client)
        self.openbb_config = config
        self._obb = self._try_import_obb()

    @staticmethod
    def _try_import_obb() -> Optional[Any]:
        """Try to import the OpenBB App, returning None if not installed.

        Importing ``openbb`` is expensive (loads every registered
        extension), so we do it once at construction time. If the user
        did not install the ``openbb`` optional extra we log a warning
        and disable the scraper instead of raising.
        """
        try:
            from openbb import obb
            return obb
        except ImportError:
            logger.warning(
                "OpenBB source is enabled but the 'openbb' package is not "
                "installed. Install it with: "
                "uv pip install --only-binary=:all: openbb"
            )
            return None

    async def fetch(self, since: datetime) -> List[ContentItem]:
        """Fetch items from all enabled OpenBB watchlists.

        Args:
            since: Only return items published strictly after this time.

        Returns:
            Deduplicated list of content items across all watchlists.
        """
        if not self._obb or not self.openbb_config.enabled:
            return []

        since_utc = self._ensure_utc(since)
        seen_urls: set[str] = set()
        items: List[ContentItem] = []

        for watchlist in self.openbb_config.watchlists:
            if not watchlist.enabled or not watchlist.symbols:
                continue
            try:
                fetched = await self._fetch_watchlist(watchlist, since_utc)
            except Exception as exc:
                logger.warning(
                    "OpenBB watchlist '%s' failed: %s",
                    watchlist.name,
                    exc,
                )
                continue
            for item in fetched:
                url_key = str(item.url)
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                items.append(item)

        return items

    async def _fetch_watchlist(
        self,
        watchlist: OpenBBWatchlist,
        since_utc: datetime,
    ) -> List[ContentItem]:
        """Fetch news for one watchlist via ``obb.news.company()``."""
        symbols_param = ",".join(watchlist.symbols)
        response = await asyncio.to_thread(
            self._obb.news.company,
            symbol=symbols_param,
            limit=watchlist.fetch_limit,
            provider=watchlist.provider,
        )
        results = getattr(response, "results", None) or []
        items: List[ContentItem] = []
        for raw in results:
            item = self._raw_to_item(raw, watchlist, since_utc)
            if item is not None:
                items.append(item)
        return items

    def _raw_to_item(
        self,
        raw: Any,
        watchlist: OpenBBWatchlist,
        since_utc: datetime,
    ) -> Optional[ContentItem]:
        """Map one OpenBB news record into a ContentItem.

        Returns None when the record is too old, has no URL, or fails
        validation. OpenBB returns Pydantic models, so we read attributes
        directly and defensively.
        """
        url = self._coerce_url(getattr(raw, "url", None))
        if not url:
            return None

        published = self._coerce_datetime(getattr(raw, "date", None))
        if published is None or published <= since_utc:
            return None

        title = (getattr(raw, "title", None) or "").strip()
        if not title:
            return None

        body = getattr(raw, "body", None) or getattr(raw, "excerpt", None)
        author = getattr(raw, "author", None)
        raw_symbols = getattr(raw, "symbols", None) or ""
        symbols = self._parse_symbols(raw_symbols) or list(watchlist.symbols)

        native_id = self._derive_native_id(url, published)
        meta = {
            "watchlist": watchlist.name,
            "provider": watchlist.provider,
            "symbols": symbols,
            "category": watchlist.category,
        }

        return ContentItem(
            id=self._generate_id("openbb", "news", native_id),
            source_type=self.SOURCE_TYPE,
            title=title,
            url=url,
            content=body,
            author=author or (symbols[0] if symbols else None),
            published_at=published,
            metadata={k: v for k, v in meta.items() if v is not None},
        )

    @staticmethod
    def _ensure_utc(moment: datetime) -> datetime:
        if moment.tzinfo is None:
            return moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc)

    @staticmethod
    def _coerce_datetime(value: Any) -> Optional[datetime]:
        """Normalize whatever OpenBB returns for `date` into aware UTC."""
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _coerce_url(value: Any) -> Optional[str]:
        if not value:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _parse_symbols(raw_symbols: Any) -> List[str]:
        if isinstance(raw_symbols, str):
            parts: Iterable[str] = raw_symbols.split(",")
        elif isinstance(raw_symbols, (list, tuple, set)):
            parts = raw_symbols
        else:
            return []
        cleaned = [str(p).strip().upper() for p in parts if str(p).strip()]
        seen: set[str] = set()
        unique: List[str] = []
        for sym in cleaned:
            if sym in seen:
                continue
            seen.add(sym)
            unique.append(sym)
        return unique

    @staticmethod
    def _derive_native_id(url: str, published: datetime) -> str:
        """Build a stable id from url + timestamp to survive URL mirrors."""
        return f"{published.strftime('%Y%m%dT%H%M%S')}::{url}"
