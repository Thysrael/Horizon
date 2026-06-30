from datetime import datetime, timezone

import httpx
import asyncio

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
