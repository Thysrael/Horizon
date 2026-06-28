"""GDELT 2.0 DOC API scraper.

Pulls recent global news articles from the key-less GDELT 2.0 DOC API
(https://api.gdeltproject.org/api/v2/doc/doc) and maps them into
ContentItem instances so the rest of the Horizon pipeline (deduplication,
AI scoring, enrichment, summarization) treats them the same way as RSS or
Hacker News items.

Design notes:

* No API key is required; GDELT is fully open. The DOC API caps results at
  250 records per request, so `max_records` is kept modest by default.
* GDELT expresses source-language and source-country filters as query
  operators (``sourcelang:`` / ``sourcecountry:``) rather than separate
  parameters, so they are appended to the query string.
* GDELT can return non-JSON or empty bodies on transient errors, so the
  ``.json()`` call is guarded and an empty/missing ``articles`` key yields
  an empty list rather than raising.
* A single malformed article is skipped, not allowed to abort the batch.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

import httpx

from .base import BaseScraper
from ..models import ContentItem, GDELTConfig, SourceType

logger = logging.getLogger(__name__)


class GDELTScraper(BaseScraper):
    """Scraper backed by the GDELT 2.0 DOC API."""

    SOURCE_TYPE = SourceType.GDELT
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, config: GDELTConfig, http_client: httpx.AsyncClient):
        """Initialize the scraper.

        Args:
            config: GDELT source configuration.
            http_client: Shared async HTTP client.
        """
        super().__init__({"gdelt": config}, http_client)
        self.gdelt_config = config

    async def fetch(self, since: datetime) -> List[ContentItem]:
        """Fetch articles from the GDELT DOC API.

        Args:
            since: Only fetch items published after this time (used to derive
                the GDELT ``startdatetime`` unless ``timespan`` is set).

        Returns:
            List[ContentItem]: Fetched content items.
        """
        if not self.gdelt_config.enabled:
            return []

        query = (self.gdelt_config.query or "").strip()
        if not query:
            return []

        # GDELT expresses language/country as query operators.
        if self.gdelt_config.language:
            query = f"{query} sourcelang:{self.gdelt_config.language}"
        if self.gdelt_config.country:
            query = f"{query} sourcecountry:{self.gdelt_config.country}"

        params: dict[str, Any] = {
            "query": query,
            "mode": self.gdelt_config.mode,
            "format": "json",
            "maxrecords": self.gdelt_config.max_records,
            "sort": "datedesc",
        }

        # timespan takes precedence over an explicit start/end window.
        if self.gdelt_config.timespan:
            params["timespan"] = self.gdelt_config.timespan
        else:
            since_utc = self._ensure_utc(since)
            now_utc = datetime.now(timezone.utc)
            params["startdatetime"] = since_utc.strftime("%Y%m%d%H%M%S")
            params["enddatetime"] = now_utc.strftime("%Y%m%d%H%M%S")

        try:
            response = await self.client.get(
                self.BASE_URL, params=params, follow_redirects=True
            )
            response.raise_for_status()

            try:
                payload = response.json()
            except Exception as exc:
                logger.warning("GDELT returned a non-JSON body: %s", exc)
                return []

            if not isinstance(payload, dict):
                return []

            articles = payload.get("articles")
            if not articles:
                return []

            items: List[ContentItem] = []
            for raw in articles:
                item = self._raw_to_item(raw)
                if item is not None:
                    items.append(item)
            return items

        except httpx.HTTPError as exc:
            logger.warning("Error fetching GDELT articles: %s", exc)
            return []
        except Exception as exc:
            logger.warning("Error parsing GDELT response: %s", exc)
            return []

    def _raw_to_item(self, raw: Any) -> Optional[ContentItem]:
        """Map one GDELT article record into a ContentItem.

        Returns None when the record has no URL/title or an unparseable
        ``seendate`` (published_at is required), so a single bad article is
        skipped rather than aborting the batch.
        """
        if not isinstance(raw, dict):
            return None

        url = (raw.get("url") or "").strip()
        title = (raw.get("title") or "").strip()
        if not url or not title:
            return None

        seendate = (raw.get("seendate") or "").strip()
        published = self._parse_seendate(seendate)
        if published is None:
            return None

        native_id = f"{seendate}::{url}"
        meta = {
            "domain": raw.get("domain"),
            "sourcecountry": raw.get("sourcecountry"),
            "language": raw.get("language"),
            "query": self.gdelt_config.query,
            "category": self.gdelt_config.category,
        }

        try:
            return ContentItem(
                id=self._generate_id("gdelt", "article", native_id),
                source_type=self.SOURCE_TYPE,
                title=title,
                url=url,
                content=None,
                author=raw.get("domain"),
                published_at=published,
                metadata={k: v for k, v in meta.items() if v is not None},
            )
        except Exception as exc:
            logger.warning("Skipping invalid GDELT article %s: %s", url, exc)
            return None

    @staticmethod
    def _parse_seendate(value: str) -> Optional[datetime]:
        """Parse a GDELT ``seendate`` ("YYYYMMDDTHHMMSSZ") into aware UTC."""
        if not value:
            return None
        try:
            dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        except (ValueError, TypeError):
            return None
        return dt.replace(tzinfo=timezone.utc)

    @staticmethod
    def _ensure_utc(moment: datetime) -> datetime:
        if moment.tzinfo is None:
            return moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc)
