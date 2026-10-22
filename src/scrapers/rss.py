"""RSS feed scraper implementation."""

import calendar
import hashlib
import os
import re
from datetime import datetime, timezone
from typing import List, Optional
from email.utils import parsedate_to_datetime
import httpx
import feedparser

from .base import BaseScraper, FetchResult
from ..extractors import ExtractorRegistry
from ..models import ContentItem, SourceType, RSSSourceConfig

class RSSScraper(BaseScraper):
    """Scraper for RSS/Atom feeds."""

    def __init__(
        self,
        sources: List[RSSSourceConfig],
        http_client: httpx.AsyncClient,
        extractors: Optional[ExtractorRegistry] = None,
    ):
        """Initialize RSS scraper.

        Args:
            sources: List of RSS feed configurations
            http_client: Shared async HTTP client
            extractors: Optional registry of content extractors for full article fetching
        """
        super().__init__({"sources": sources}, http_client)
        self._extractors = extractors

    async def fetch(self, since: datetime) -> FetchResult:
        """Fetch RSS feed items.

        Args:
            since: Only fetch items published after this time

        Returns:
            FetchResult: Items and per-feed failures
        """
        result = FetchResult()
        sources = self.config["sources"]

        for source in sources:
            if not source.enabled:
                continue

            await result.collect(source.name, self._fetch_feed(source, since))

        return result

    async def _fetch_feed(
        self, source: RSSSourceConfig, since: datetime
    ) -> List[ContentItem]:
        """Fetch items from a single RSS feed.

        Args:
            source: RSS feed configuration
            since: Only fetch items after this time

        Returns:
            List[ContentItem]: Feed content items
        """
        items = []

        # Expand environment variables in URL (e.g. ${LWN_TOKEN})
        feed_url = re.sub(
            r"\$\{(\w+)\}",
            lambda m: os.environ.get(m.group(1), m.group(0)).strip(),
            str(source.url),
        )
        response = await self.client.get(feed_url, follow_redirects=True)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        if feed.bozo and not feed.entries:
            raise ValueError("Invalid RSS/Atom feed")

        for entry in feed.entries:
            published_at = self._parse_date(entry)
            if not published_at or published_at < since:
                continue

            feed_id = str(source.url).split("//")[1].replace("/", "_")
            entry_id = entry.get("id", entry.get("link", ""))
            entry_hash = hashlib.sha256(str(entry_id).encode("utf-8")).hexdigest()[:16]
            content = self._extract_content(entry)

            if source.content_extractor and self._extractors:
                extractor = self._extractors.get(source.content_extractor)
                if extractor:
                    url = entry.get("link", "")
                    if url:
                        full = await extractor.extract(url, self.client)
                        if full:
                            content = full

            items.append(ContentItem(
                id=self._generate_id("rss", feed_id, entry_hash),
                source_type=SourceType.RSS,
                title=entry.get("title", "Untitled"),
                url=entry.get("link", str(source.url)),
                content=content,
                author=entry.get("author", source.name),
                published_at=published_at,
                profile=source.profile,
                metadata={
                    "feed_name": source.name,
                    "category": source.category,
                    "tags": [tag.term for tag in entry.get("tags", [])],
                },
            ))

        return items

    def _parse_date(self, entry: dict) -> datetime:
        """Parse publication date from feed entry.

        Args:
            entry: Feed entry data

        Returns:
            datetime: Parsed publication date or None
        """
        # Try different date fields
        for field in ["published", "updated", "created"]:
            if field in entry:
                try:
                    # Try parsing structured time first
                    if f"{field}_parsed" in entry and entry[f"{field}_parsed"]:
                        return datetime.fromtimestamp(
                            calendar.timegm(entry[f"{field}_parsed"]), tz=timezone.utc
                        )
                    # Fallback to string parsing
                    date_str = entry[field]
                    parsed_date = parsedate_to_datetime(date_str)
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    return parsed_date
                except Exception:
                    continue

        return None

    def _extract_content(self, entry: dict) -> str:
        """Extract text content from feed entry.

        Args:
            entry: Feed entry data

        Returns:
            str: Extracted text content
        """
        content = entry.get("content", [])
        if not isinstance(content, (list, tuple)):
            content = []
        candidates = []
        for part in content:
            if not isinstance(part, dict):
                continue
            media_type = part.get("type", "")
            if not isinstance(media_type, str):
                continue
            media_type = media_type.split(";", 1)[0].strip().lower()
            if media_type and not (
                media_type.startswith("text/")
                or media_type in ("html", "xhtml", "application/xhtml+xml")
            ):
                continue
            candidates.append(part.get("value"))
        # max keeps the first candidate on ties, so prefer content alternatives.
        candidates.extend([entry.get("summary"), entry.get("description")])
        return max(
            (value for value in candidates if isinstance(value, str) and value.strip()),
            key=len,
            default="",
        )
