import asyncio
from datetime import datetime, timezone

import httpx

from src.models import GitHubSourceConfig
from src.scrapers.github import GitHubScraper


def _fetch_events(events):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=events)
        )) as client:
            source = GitHubSourceConfig(type="user_events", username="torvalds")
            scraper = GitHubScraper([source], client)
            return await scraper.fetch(datetime(2026, 11, 1, tzinfo=timezone.utc))

    return asyncio.run(run())


def _push_event(payload):
    return {
        "id": "1",
        "type": "PushEvent",
        "created_at": "2026-11-02T12:00:00Z",
        "repo": {"name": "torvalds/linux"},
        "payload": payload,
    }


def test_push_event_without_commits_does_not_claim_zero_commits():
    # The public Events API no longer includes "commits" in PushEvent payloads.
    result = _fetch_events([_push_event({
        "before": "aaa111",
        "head": "bbb222",
        "push_id": 123,
        "ref": "refs/heads/master",
        "repository_id": 2325298,
    })])

    assert result.status == "success"
    [item] = result.items
    assert item.title == "torvalds pushed to torvalds/linux (master)"
    assert item.content == ""


def test_push_event_with_commits_keeps_count_and_messages():
    result = _fetch_events([_push_event({
        "ref": "refs/heads/master",
        "commits": [{"message": "first"}, {"message": "second"}],
    })])

    [item] = result.items
    assert item.title == "torvalds pushed 2 commit(s) to torvalds/linux"
    assert item.content == "first\nsecond"
    assert str(item.url) == "https://github.com/torvalds/linux"
