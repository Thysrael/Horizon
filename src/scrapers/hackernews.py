"""Hacker News scraper implementation."""

import re
from datetime import datetime, timezone
from typing import List, Optional
import asyncio
import httpx

from .base import BaseScraper, FetchResult
from ..models import ContentItem, SourceType, HackerNewsConfig

# Max top-level comments to fetch per story
TOP_COMMENTS_LIMIT = 5


class HackerNewsScraper(BaseScraper):
    """Scraper for Hacker News stories with top comments."""

    def __init__(self, config: HackerNewsConfig, http_client: httpx.AsyncClient):
        super().__init__(config.model_dump(), http_client)
        self.base_url = "https://hacker-news.firebaseio.com/v0"

    async def fetch(self, since: datetime) -> FetchResult:
        result = FetchResult()
        if not self.config.get("enabled", True):
            return result

        try:
            response = await self.client.get(f"{self.base_url}/topstories.json")
            response.raise_for_status()
            story_ids = response.json()

            if not isinstance(story_ids, list):
                raise ValueError("Hacker News returned an invalid story list")
        except Exception as exc:
            result.fail("topstories", exc)
            return result

        await asyncio.gather(*(
            result.collect(f"story:{story_id}", self._fetch_story_item(story_id, since))
            for story_id in story_ids[:self.config.get("fetch_top_stories", 30)]
        ))
        return result

    async def _fetch_story_item(self, story_id: int, since: datetime) -> List[ContentItem]:
        story = await self._fetch_story(story_id)
        if not story or story.get("score", 0) < self.config.get("min_score", 100):
            return []
        if datetime.fromtimestamp(story["time"], tz=timezone.utc) < since:
            return []
        comments = await self._fetch_comments(story.get("kids", [])[:TOP_COMMENTS_LIMIT])
        return [self._parse_story(story, comments)]

    async def _fetch_story(self, story_id: int) -> Optional[dict]:
        response = await self.client.get(f"{self.base_url}/item/{story_id}.json")
        response.raise_for_status()
        return response.json()

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

        return ContentItem(
            id=self._generate_id("hackernews", "story", str(story_id)),
            source_type=SourceType.HACKERNEWS,
            title=title,
            url=url,
            content=content,
            author=author,
            published_at=published_at,
            profile=self.config.get("profile"),
            metadata={
                "score": story.get("score", 0),
                "descendants": story.get("descendants", 0),
                "type": story.get("type", "story"),
                "discussion_url": hn_discussion_url,
                "comment_count": len(comments),
                "category": self.config.get("category"),
            }
        )
