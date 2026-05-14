"""OSS Insight trending repos scraper.

Fetches star-gain rankings from api.ossinsight.io and emits them as
ContentItems. An optional keyword filter narrows results to repos whose
description, repo name, or collection names match at least one configured
substring (case-insensitive). Without keywords, all trending repos in the
configured languages flow through.
"""

from datetime import datetime, timezone
from typing import List, Optional

import httpx

from ..models import ContentItem, OSSInsightConfig, SourceType
from .base import BaseScraper


class OSSInsightScraper(BaseScraper):
    """Scraper for OSS Insight trending repositories endpoint."""

    BASE_URL = "https://api.ossinsight.io/v1/trends/repos"

    def __init__(self, config: OSSInsightConfig, http_client: httpx.AsyncClient):
        """Initialize scraper.

        Args:
            config: OSS Insight source configuration
            http_client: Shared async HTTP client
        """
        super().__init__(config, http_client)
        self.cfg: OSSInsightConfig = config
        self._keywords_lower = [kw.lower() for kw in self.cfg.keywords if kw]

    async def fetch(self, since: datetime) -> List[ContentItem]:
        """Fetch trending repos for each configured language and apply filters."""
        if not self.cfg.enabled:
            return []

        items: List[ContentItem] = []
        seen_ids: set[str] = set()

        for lang in self.cfg.languages:
            rows = await self._fetch_period(self.cfg.period, lang)
            for row in rows:
                item = self._row_to_item(row, lang)
                if item is None:
                    continue
                if item.id in seen_ids:
                    continue
                if self.cfg.min_stars and self._stars_int(row) < self.cfg.min_stars:
                    continue
                if self._keywords_lower and not self._matches_keywords(row):
                    continue
                seen_ids.add(item.id)
                items.append(item)

        items.sort(key=lambda x: x.metadata.get("stars_gained", 0), reverse=True)
        return items[: self.cfg.max_items]

    async def _fetch_period(self, period: str, language: str) -> List[dict]:
        """Call OSS Insight API for one (period, language) combo."""
        params = {"period": period, "language": language}
        try:
            response = await self.client.get(
                self.BASE_URL,
                params=params,
                headers={"Accept": "application/json", "User-Agent": "Horizon/1.0"},
                timeout=20.0,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        payload = response.json()
        data = payload.get("data") or {}
        rows = data.get("rows") or []
        return rows

    def _row_to_item(self, row: dict, language: str) -> Optional[ContentItem]:
        """Convert a raw OSS Insight row into a ContentItem."""
        repo_name = row.get("repo_name")
        repo_id = row.get("repo_id")
        if not repo_name or not repo_id:
            return None

        stars_gained = self._stars_int(row)
        description = (row.get("description") or "").strip()
        primary_language = row.get("primary_language") or language

        title = f"{repo_name} (+{stars_gained}⭐ {self.cfg.period})"
        url = f"https://github.com/{repo_name}"

        content_lines = [
            f"Trending GitHub repo: {repo_name}",
            f"Stars gained ({self.cfg.period}): {stars_gained}",
            f"Forks gained: {row.get('forks', 0)}",
            f"Pushes: {row.get('pushes', 0)}",
            f"Pull requests: {row.get('pull_requests', 0)}",
            f"Language: {primary_language}",
        ]
        if description:
            content_lines.append("")
            content_lines.append(description)
        collections = row.get("collection_names")
        if collections:
            content_lines.append("")
            content_lines.append(f"OSS Insight collections: {collections}")

        return ContentItem(
            id=self._generate_id(SourceType.OSSINSIGHT.value, "trending", str(repo_id)),
            source_type=SourceType.OSSINSIGHT,
            title=title,
            url=url,
            content="\n".join(content_lines),
            author=repo_name.split("/")[0] if "/" in repo_name else None,
            published_at=datetime.now(timezone.utc),
            metadata={
                "repo": repo_name,
                "stars_gained": stars_gained,
                "forks_gained": self._int(row.get("forks")),
                "pushes": self._int(row.get("pushes")),
                "pull_requests": self._int(row.get("pull_requests")),
                "primary_language": primary_language,
                "period": self.cfg.period,
                "collection_names": collections,
                "description": description,
            },
        )

    @staticmethod
    def _stars_int(row: dict) -> int:
        """Pull star count out of a row, coercing to int."""
        return OSSInsightScraper._int(row.get("stars"))

    @staticmethod
    def _int(value) -> int:
        """Best-effort conversion to int, defaulting to 0."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _matches_keywords(self, row: dict) -> bool:
        """Case-insensitive substring match against description, name, collections."""
        haystack = " ".join(
            [
                (row.get("description") or "").lower(),
                (row.get("collection_names") or "").lower(),
                (row.get("repo_name") or "").lower(),
            ]
        )
        return any(kw in haystack for kw in self._keywords_lower)
