"""OSS Insight trending repos scraper.

Fetches star-gain rankings from api.ossinsight.io and emits them as
ContentItems. An optional keyword filter narrows results to repos whose
description, repo name, or collection names match at least one configured
substring (case-insensitive). Without keywords, all trending repos in the
configured languages flow through. If OSS Insight is unavailable, falls back
to GitHub repository search so the OSS bucket can still receive candidates.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, cast

import httpx

from ..models import ContentItem, OSSInsightConfig, SourceType
from .base import BaseScraper


class OSSInsightScraper(BaseScraper):
    """Scraper for OSS Insight trending repositories endpoint."""

    BASE_URL = "https://api.ossinsight.io/v1/trends/repos"
    GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

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
            if not rows:
                rows = await self._fetch_github_search(lang, since)
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

    async def _fetch_github_search(self, language: str, since: datetime) -> List[dict]:
        """Fallback to GitHub repository search when OSS Insight is unavailable."""
        # GitHub Search rejects queries with more than five boolean operators.
        # Query a few compact keyword chunks instead of one huge OR clause.
        keywords = [kw for kw in (self.cfg.keywords or ["AI", "LLM", "agent"]) if kw]
        keyword_chunks = [keywords[i : i + 5] for i in range(0, min(len(keywords), 10), 5)]
        created_since = since.date().isoformat()
        rows = []
        seen: set[int] = set()
        for chunk in keyword_chunks:
            query_parts = [
                " OR ".join(chunk),
                "in:name,description",
                f"stars:>={max(self.cfg.min_stars, 1)}",
                f"created:>={created_since}",
            ]
            if language and language.lower() != "all":
                query_parts.append(f"language:{language}")

            try:
                response = await self.client.get(
                    self.GITHUB_SEARCH_URL,
                    params={
                        "q": " ".join(query_parts),
                        "sort": "stars",
                        "order": "desc",
                        "per_page": min(max(self.cfg.max_items, 1), 30),
                    },
                    headers={"Accept": "application/vnd.github+json", "User-Agent": "Horizon/1.0"},
                    timeout=20.0,
                )
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            payload = response.json()
            for repo in payload.get("items") or []:
                repo_id = repo.get("id")
                if not repo_id or repo_id in seen:
                    continue
                seen.add(repo_id)
                rows.append({
                    "repo_id": repo_id,
                    "repo_name": repo.get("full_name"),
                    "html_url": repo.get("html_url"),
                    "description": repo.get("description") or "",
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "pushes": 0,
                    "pull_requests": 0,
                    "primary_language": repo.get("language") or language,
                    "collection_names": "GitHub search fallback",
                    "fallback": "github_search",
                    "pushed_at": repo.get("pushed_at"),
                    "owner": (repo.get("owner") or {}).get("login"),
                })
        return rows

    def _row_to_item(self, row: dict, language: str) -> Optional[ContentItem]:
        """Convert a raw OSS Insight/GitHub row into a ContentItem."""
        repo_name = row.get("repo_name")
        repo_id = row.get("repo_id")
        if not repo_name or not repo_id:
            return None

        stars_gained = self._stars_int(row)
        description = (row.get("description") or "").strip()
        primary_language = row.get("primary_language") or language
        is_fallback = row.get("fallback") == "github_search"

        suffix = "GitHub search fallback" if is_fallback else self.cfg.period
        title = f"{repo_name} ({stars_gained}⭐ {suffix})"
        url = row.get("html_url") or f"https://github.com/{repo_name}"

        content_lines = [
            f"Trending GitHub repo: {repo_name}",
            f"Stars ({suffix}): {stars_gained}",
            f"Forks: {row.get('forks', 0)}",
            f"Pushes: {row.get('pushes', 0)}",
            f"Pull requests: {row.get('pull_requests', 0)}",
            f"Language: {primary_language}",
        ]
        if row.get("pushed_at"):
            content_lines.append(f"Last pushed: {row['pushed_at']}")
        if description:
            content_lines.append("")
            content_lines.append(description)
        collections = row.get("collection_names")
        if collections:
            content_lines.append("")
            content_lines.append(f"OSS Insight collections: {collections}")

        metadata: dict[str, Any] = {
            "repo": repo_name,
            "stars_gained": stars_gained,
            "forks_gained": self._int(row.get("forks")),
            "pushes": self._int(row.get("pushes")),
            "pull_requests": self._int(row.get("pull_requests")),
            "primary_language": primary_language,
            "period": self.cfg.period,
            "collection_names": collections,
            "description": description,
        }
        if self.cfg.category:
            metadata["category"] = self.cfg.category
        if is_fallback:
            metadata["fallback"] = "github_search"
            metadata["pushed_at"] = row.get("pushed_at")

        return ContentItem(
            id=self._generate_id(SourceType.OSSINSIGHT.value, "trending", str(repo_id)),
            source_type=SourceType.OSSINSIGHT,
            title=title,
            url=cast(Any, url),
            content="\n".join(content_lines),
            author=row.get("owner") or (repo_name.split("/")[0] if "/" in repo_name else None),
            published_at=datetime.now(timezone.utc),
            metadata=metadata,
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
