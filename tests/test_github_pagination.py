import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from src.models import GitHubSourceConfig
from src.scrapers.github import GitHubScraper


@pytest.mark.parametrize("source", [
    GitHubSourceConfig(type="repo_releases", owner="org", repo="repo"),
    GitHubSourceConfig(type="user_events", username="user"),
])
def test_github_reads_next_page_without_losing_new_items(source):
    requests = []

    def handler(request):
        requests.append(request)
        page = int(request.url.params.get("page", "1"))
        if source.type == "repo_releases":
            item = {"id": page, "published_at": "2026-11-01T12:00:00Z", "tag_name": f"v{page}",
                    "html_url": f"https://github.com/org/repo/releases/tag/v{page}", "author": {"login": "author"}}
        else:
            item = {"id": str(page), "created_at": "2026-11-01T12:00:00Z", "type": "PublicEvent",
                    "repo": {"name": f"org/repo{page}"}, "payload": {}}
        headers = {"Link": '<https://api.github.com/example?page=2>; rel="next"'} if page == 1 else {}
        return httpx.Response(200, json=[item], headers=headers)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await GitHubScraper([source], client).fetch(datetime(2026, 10, 31, tzinfo=timezone.utc))

    result = asyncio.run(run())
    assert result.status == "success"
    assert len(result.items) == 2
    assert len(requests) == 2
    assert requests[0].url.path == requests[1].url.path
    assert [r.url.params["page"] for r in requests] == ["1", "2"]
    assert all(r.url.params["per_page"] == "100" for r in requests)


def test_empty_page_stops_even_with_stale_next_link():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[], headers={
            "Link": '<https://api.github.com/example?page=2>; rel="next"',
        })

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await GitHubScraper([], client)._fetch_pages("https://api.github.com/example")

    assert asyncio.run(run()) == []
    assert len(requests) == 1
