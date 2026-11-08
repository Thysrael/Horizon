"""RSS feed scraper implementation."""

import asyncio
import calendar
import hashlib
import logging
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

logger = logging.getLogger(__name__)

# Identify feed requests: some publishers reject httpx's default User-Agent.
RSS_USER_AGENT = "Horizon/0.1.0 (+https://github.com/Thysrael/Horizon)"
MAX_CONCURRENT_FEEDS = 3

# Rate-limited feeds (e.g. Reddit RSS answers bursts with 429) are retried with
# linear backoff, honouring a numeric Retry-After header up to the cap.
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF_SEC = 15.0
RATE_LIMIT_MAX_WAIT_SEC = 60.0


def _rate_limit_delay(response: httpx.Response, attempt: int) -> float:
    """Seconds to wait before retry number ``attempt`` (1-based)."""
    retry_after = response.headers.get("Retry-After", "")
    try:
        delay = float(retry_after)
    except ValueError:
        delay = RATE_LIMIT_BACKOFF_SEC * attempt
    return max(0.0, min(delay, RATE_LIMIT_MAX_WAIT_SEC))


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
        sources = [source for source in self.config["sources"] if source.enabled]
        slots = asyncio.Semaphore(MAX_CONCURRENT_FEEDS)
        host_locks = {source.url.host: asyncio.Lock() for source in sources}

        async def fetch_source(source: RSSSourceConfig) -> FetchResult:
            # Wait for the host before occupying a global slot, so queued feeds
            # from one host cannot prevent other hosts from making progress.
            async with host_locks[source.url.host], slots:
                try:
                    return await self._fetch_feed(source, since)
                except Exception as exc:
                    failure = FetchResult()
                    failure.fail(source.name, exc)
                    return failure

        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(fetch_source(source)) for source in sources]

        # Preserve configured feed order regardless of completion order.
        for task in tasks:
            feed_result = task.result()
            result.items.extend(feed_result.items)
            result.failures.update(feed_result.failures)
            result.successful += feed_result.successful

        return result

    async def _fetch_feed(
        self, source: RSSSourceConfig, since: datetime
    ) -> FetchResult:
        """Fetch items from a single RSS feed.

        Args:
            source: RSS feed configuration
            since: Only fetch items after this time

        Returns:
            FetchResult: Feed content items and entry failures
        """
        result = FetchResult()

        # Expand environment variables in URL (e.g. ${LWN_TOKEN})
        feed_url = re.sub(
            r"\$\{(\w+)\}",
            lambda m: os.environ.get(m.group(1), m.group(0)).strip(),
            str(source.url),
        )
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            response = await self.client.get(
                feed_url,
                follow_redirects=True,
                headers={"User-Agent": RSS_USER_AGENT},
            )
            if response.status_code != 429 or attempt == RATE_LIMIT_RETRIES:
                break
            delay = _rate_limit_delay(response, attempt + 1)
            logger.info(
                "RSS feed %s rate-limited (429); retrying in %.0fs (%d/%d)",
                source.name, delay, attempt + 1, RATE_LIMIT_RETRIES,
            )
            await asyncio.sleep(delay)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        if feed.bozo and not feed.entries:
            raise ValueError("Invalid RSS/Atom feed")

        for ordinal, entry in enumerate(feed.entries, start=1):
            try:
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

                result.items.append(ContentItem(
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
            except Exception as exc:
                label = f"{source.name}/entry:{ordinal}"
                # Avoid multiline validation details that include entry values.
                reason = str(exc).partition("\n")[0][:200]
                error = f"{type(exc).__name__}: {reason}"
                result.failures[label] = error
                logger.warning("Skipping RSS entry %s: %s", label, error)

        # A feed with only rejected entries is not a successful empty response.
        result.successful = int(bool(result.items) or not result.failures)
        return result

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
