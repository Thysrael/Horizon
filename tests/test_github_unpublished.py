import asyncio
from datetime import datetime, timezone

import httpx

from src.models import GitHubSourceConfig
from src.scrapers.github import GitHubScraper


def test_unpublished_releases_do_not_discard_published_releases():
    published = {
        "id": 2, "draft": False, "published_at": "2026-11-01T12:00:00Z",
        "tag_name": "v2", "html_url": "https://github.com/org/repo/releases/tag/v2",
        "author": {"login": "maintainer"}, "body": None,
    }
    releases = [
        {**published, "id": 1, "draft": True, "published_at": None},
        {**published, "id": 3, "published_at": None},
        published,
    ]

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=releases)
        )) as client:
            scraper = GitHubScraper([GitHubSourceConfig(type="repo_releases", owner="org", repo="repo")], client)
            return await scraper.fetch(datetime(2026, 10, 31, tzinfo=timezone.utc))

    result = asyncio.run(run())
    assert result.status == "success"
    assert [item.title for item in result.items] == ["org/repo released v2"]
    assert result.items[0].content is None
