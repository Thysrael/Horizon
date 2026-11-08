import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from src.models import RSSSourceConfig
from src.scrapers import rss
from src.scrapers.rss import RSSScraper


SINCE = datetime(2026, 11, 1, tzinfo=timezone.utc)
FEED = """<rss version="2.0"><channel><title>Test</title><item>
<guid>one</guid><title>Article</title><link>https://example.com/article</link>
<pubDate>Mon, 02 Nov 2026 09:00:00 GMT</pubDate>
<description>Content</description></item></channel></rss>"""


def test_other_hosts_progress_during_retry_without_same_host_overlap(monkeypatch):
    async def run():
        waiting = asyncio.Event()
        other_finished = asyncio.Event()
        requests = []
        delays = []

        async def sleep(delay):
            delays.append(delay)
            waiting.set()
            await other_finished.wait()

        async def respond(request):
            path = request.url.path
            requests.append(path)
            if path == "/limited" and requests.count(path) == 1:
                return httpx.Response(429)
            if path == "/other":
                await waiting.wait()
                assert "/queued" not in requests
                other_finished.set()
            return httpx.Response(200, text=FEED)

        monkeypatch.setattr(rss.asyncio, "sleep", sleep)
        monkeypatch.setattr(rss, "MAX_CONCURRENT_FEEDS", 2)
        sources = [
            RSSSourceConfig(name="limited", url="https://a.example/limited"),
            RSSSourceConfig(name="queued", url="https://a.example/queued"),
            RSSSourceConfig(name="other", url="https://b.example/other"),
            RSSSourceConfig(name="disabled", url="https://b.example/disabled", enabled=False),
        ]
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await asyncio.wait_for(RSSScraper(sources, client).fetch(SINCE), 2)
        assert delays == [15.0]
        assert requests == ["/limited", "/other", "/limited", "/queued"]
        assert result.successful == 3
        assert [item.metadata["feed_name"] for item in result.items] == ["limited", "queued", "other"]

    asyncio.run(run())


def test_cancelling_fetch_drains_active_requests():
    async def run():
        started = set()
        cancelled = set()
        ready = asyncio.Event()

        async def respond(request):
            host = request.url.host
            started.add(host)
            if len(started) == 2:
                ready.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.add(host)

        sources = [
            RSSSourceConfig(name=host, url=f"https://{host}.example/feed")
            for host in "ab"
        ]
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            task = asyncio.create_task(RSSScraper(sources, client).fetch(SINCE))
            try:
                await asyncio.wait_for(ready.wait(), 2)
            finally:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
        assert cancelled == started == {"a.example", "b.example"}

    asyncio.run(run())


def test_feed_concurrency_is_bounded_and_failures_are_isolated(monkeypatch):
    async def run():
        started = 0
        active = 0
        peak = 0
        full = asyncio.Event()
        release = asyncio.Event()

        async def respond(request):
            nonlocal started, active, peak
            started += 1
            active += 1
            peak = max(peak, active)
            if active == 2:
                full.set()
            try:
                await release.wait()
                if request.url.host == "a.example":
                    return httpx.Response(403)
                return httpx.Response(200, text=FEED)
            finally:
                active -= 1

        monkeypatch.setattr(rss, "MAX_CONCURRENT_FEEDS", 2)
        sources = [RSSSourceConfig(name=host, url=f"https://{host}.example/feed") for host in "abcd"]
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            async with asyncio.TaskGroup() as group:
                task = group.create_task(RSSScraper(sources, client).fetch(SINCE))
                try:
                    await asyncio.wait_for(full.wait(), 2)
                    assert started == 2
                finally:
                    release.set()
            result = task.result()
        assert peak == 2
        assert result.successful == 3
        assert list(result.failures) == ["a"]
        assert [item.metadata["feed_name"] for item in result.items] == ["b", "c", "d"]

    asyncio.run(run())
