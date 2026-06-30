from datetime import datetime, timezone

import asyncio
import httpx

from src.models import OSSInsightConfig
from src.scrapers.ossinsight import OSSInsightScraper


def test_ossinsight_items_carry_configured_category() -> None:
    payload = {
        "data": {
            "rows": [
                {
                    "repo_id": 123,
                    "repo_name": "example/agent-tool",
                    "description": "LLM agent workflow tool",
                    "stars": 12,
                    "forks": 1,
                    "pushes": 2,
                    "pull_requests": 3,
                    "primary_language": "Python",
                    "collection_names": "AI",
                }
            ]
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    scraper = OSSInsightScraper(
        OSSInsightConfig(
            enabled=True,
            languages=["Python"],
            keywords=["agent"],
            min_stars=1,
            max_items=5,
            category="oss",
        ),
        client,
    )

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc)))
    asyncio.run(client.aclose())

    assert len(items) == 1
    assert items[0].metadata["category"] == "oss"


def test_ossinsight_falls_back_to_github_search_when_api_fails() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.host == "api.ossinsight.io":
            return httpx.Response(500, text="upstream broken")
        if request.url.host == "api.github.com":
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": 456,
                            "full_name": "example/llm-runner",
                            "html_url": "https://github.com/example/llm-runner",
                            "description": "LLM inference runner",
                            "stargazers_count": 42,
                            "forks_count": 4,
                            "pushed_at": "2026-06-30T00:00:00Z",
                            "language": "Python",
                            "owner": {"login": "example"},
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected url: {request.url}")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    scraper = OSSInsightScraper(
        OSSInsightConfig(
            enabled=True,
            languages=["Python"],
            keywords=["llm"],
            min_stars=1,
            max_items=5,
            category="oss",
        ),
        client,
    )

    items = asyncio.run(scraper.fetch(datetime(2026, 6, 30, tzinfo=timezone.utc)))
    asyncio.run(client.aclose())

    assert any("api.ossinsight.io" in url for url in requests)
    assert any("api.github.com/search/repositories" in url for url in requests)
    assert len(items) == 1
    assert items[0].title == "example/llm-runner (42⭐ GitHub search fallback)"
    assert items[0].metadata["category"] == "oss"
    assert items[0].metadata["fallback"] == "github_search"
