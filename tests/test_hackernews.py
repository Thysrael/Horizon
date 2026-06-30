import asyncio
from datetime import datetime, timezone

import httpx

from src.models import HackerNewsConfig
from src.scrapers.hackernews import HackerNewsScraper


def _story(story_id: int, title: str, score: int = 100, url: str = "https://example.com") -> dict:
    return {
        "id": story_id,
        "type": "story",
        "title": title,
        "url": url,
        "by": "tester",
        "time": int(datetime.now(timezone.utc).timestamp()),
        "score": score,
        "descendants": 0,
        "kids": [],
    }


def test_hackernews_include_exclude_filters_and_category() -> None:
    stories = {
        1: _story(1, "New LLM inference engine", url="https://example.com/llm"),
        2: _story(2, "European digital identity policy", url="https://example.com/policy"),
        3: _story(3, "Generic TypeScript validation pattern", url="https://example.com/ts"),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/topstories.json"):
            return httpx.Response(200, json=[1, 2, 3])
        story_id = int(request.url.path.rsplit("/", 1)[-1].removesuffix(".json"))
        return httpx.Response(200, json=stories[story_id])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    scraper = HackerNewsScraper(
        HackerNewsConfig(
            enabled=True,
            fetch_top_stories=3,
            min_score=1,
            include_keywords=["LLM", "agent", "inference"],
            exclude_keywords=["digital identity", "TypeScript validation"],
            category="ai-news",
        ),
        client,
    )

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc).replace(year=2020)))
    asyncio.run(client.aclose())

    assert [item.title for item in items] == ["New LLM inference engine"]
    assert items[0].metadata["category"] == "ai-news"
    assert items[0].metadata["matched_keywords"] == ["inference", "llm"]


def test_hackernews_without_include_keywords_only_applies_excludes() -> None:
    stories = {
        1: _story(1, "Useful AI agents project"),
        2: _story(2, "Digital identity policy debate"),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/topstories.json"):
            return httpx.Response(200, json=[1, 2])
        story_id = int(request.url.path.rsplit("/", 1)[-1].removesuffix(".json"))
        return httpx.Response(200, json=stories[story_id])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    scraper = HackerNewsScraper(
        HackerNewsConfig(
            enabled=True,
            fetch_top_stories=2,
            min_score=1,
            exclude_keywords=["digital identity"],
            category="ai-news",
        ),
        client,
    )

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc).replace(year=2020)))
    asyncio.run(client.aclose())

    assert [item.title for item in items] == ["Useful AI agents project"]
    assert items[0].metadata["category"] == "ai-news"
