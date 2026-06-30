"""Hacker News scraper implementation."""

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional
import asyncio
import httpx

from .base import BaseScraper
from ..models import ContentItem, SourceType, HackerNewsConfig

logger = logging.getLogger(__name__)

# Max top-level comments to fetch per story
TOP_COMMENTS_LIMIT = 5


class HackerNewsScraper(BaseScraper):
    """Scraper for Hacker News stories with top comments."""

    def __init__(self, config: HackerNewsConfig, http_client: httpx.AsyncClient):
        super().__init__(config.model_dump(), http_client)
        self.hn_config = config
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self._include_keywords = [kw.lower() for kw in config.include_keywords if kw]
        self._exclude_keywords = [kw.lower() for kw in config.exclude_keywords if kw]

    async def fetch(self, since: datetime) -> List[ContentItem]:
        if not self.config.get("enabled", True):
            return []

        try:
            response = await self.client.get(f"{self.base_url}/topstories.json")
            response.raise_for_status()
            story_ids = response.json()

            fetch_count = self.config.get("fetch_top_stories", 30)
            story_ids = story_ids[:fetch_count]

            # Fetch story details concurrently
            tasks = [self._fetch_story(story_id) for story_id in story_ids]
            stories = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter and process stories, then fetch comments
            items = []
            min_score = self.config.get("min_score", 100)

            comment_tasks = []
            valid_stories = []

            for story in stories:
                if isinstance(story, Exception) or story is None:
                    continue
                if story.get("score", 0) < min_score:
                    continue
                published_at = datetime.fromtimestamp(story["time"], tz=timezone.utc)
                if published_at < since:
                    continue
                if not self._matches_filters(story):
                    continue
                valid_stories.append(story)
                # Queue comment fetching
                comment_ids = story.get("kids", [])[:TOP_COMMENTS_LIMIT]
                comment_tasks.append(self._fetch_comments(comment_ids))

            # Fetch all comments concurrently
            all_comments = await asyncio.gather(*comment_tasks, return_exceptions=True)

            for story, comments in zip(valid_stories, all_comments):
                if isinstance(comments, Exception):
                    comments = []
                item = self._parse_story(story, comments)
                if item:
                    items.append(item)

            return items

        except httpx.HTTPError as e:
            logger.warning("Error fetching Hacker News stories: %s", e)
            return []

    async def _fetch_story(self, story_id: int) -> Optional[dict]:
        try:
            response = await self.client.get(f"{self.base_url}/item/{story_id}.json")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    async def _fetch_comments(self, comment_ids: List[int]) -> List[dict]:
        """Fetch multiple comments concurrently."""
        if not comment_ids:
            return []

        tasks = [self._fetch_story(cid) for cid in comment_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        comments = []
        for r in results:
            if isinstance(r, dict) and r.get("text") and not r.get("deleted") and not r.get("dead"):
                comments.append(r)
        return comments

    def _parse_story(self, story: dict, comments: List[dict]) -> ContentItem:
        story_id = story["id"]
        title = story.get("title", "")
        url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
        author = story.get("by", "unknown")
        published_at = datetime.fromtimestamp(story["time"], tz=timezone.utc)

        # Build content: original text + top comments
        parts = []
        if story.get("text"):
            parts.append(story["text"])

        if comments:
            parts.append("\n--- Top Comments ---")
            for c in comments:
                commenter = c.get("by", "anon")
                text = c.get("text", "")
                # Strip HTML tags roughly
                text = re.sub(r'<[^>]+>', ' ', text).strip()
                # Truncate very long comments
                if len(text) > 500:
                    text = text[:497] + "..."
                parts.append(f"[{commenter}]: {text}")

        content = "\n\n".join(parts)
        hn_discussion_url = f"https://news.ycombinator.com/item?id={story_id}"

        metadata = {
            "score": story.get("score", 0),
            "descendants": story.get("descendants", 0),
            "type": story.get("type", "story"),
            "discussion_url": hn_discussion_url,
            "comment_count": len(comments),
        }
        if self.hn_config.category:
            metadata["category"] = self.hn_config.category
        matched_keywords = self._matched_keywords(story)
        if matched_keywords:
            metadata["matched_keywords"] = matched_keywords

        return ContentItem(
            id=self._generate_id("hackernews", "story", str(story_id)),
            source_type=SourceType.HACKERNEWS,
            title=title,
            url=url,
            content=content,
            author=author,
            published_at=published_at,
            metadata=metadata,
        )

    def _story_haystack(self, story: dict) -> str:
        """Return lower-cased story fields used for configured keyword filters."""
        return " ".join(
            str(story.get(key) or "").lower()
            for key in ("title", "url", "text")
        )

    def _matched_keywords(self, story: dict) -> list[str]:
        """Configured include keywords that matched this story."""
        haystack = self._story_haystack(story)
        return sorted({kw for kw in self._include_keywords if kw in haystack})

    def _matches_filters(self, story: dict) -> bool:
        """Apply optional include/exclude keyword filters before comment fetching."""
        haystack = self._story_haystack(story)
        if self._exclude_keywords and any(kw in haystack for kw in self._exclude_keywords):
            return False
        if self._include_keywords and not any(kw in haystack for kw in self._include_keywords):
            return False
        return True
