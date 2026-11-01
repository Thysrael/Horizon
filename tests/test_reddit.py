import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import httpx
import pytest

from src.models import RedditConfig, RedditSubredditConfig, RedditUserConfig
from src.scrapers.reddit import REDDIT_HEADERS, RedditScraper


def _make_config(fetch_comments: int = 1, profile: str | None = None) -> RedditConfig:
    return RedditConfig(
        enabled=True,
        subreddits=[
            RedditSubredditConfig(
                subreddit="LocalLLaMA",
                enabled=True,
                sort="hot",
                fetch_limit=1,
                min_score=1,
                profile=profile,
            )
        ],
        users=[],
        fetch_comments=fetch_comments,
    )


def _make_two_subreddit_config(fetch_comments: int = 0) -> RedditConfig:
    return RedditConfig(
        enabled=True,
        subreddits=[
            RedditSubredditConfig(
                subreddit="LocalLLaMA",
                enabled=True,
                sort="hot",
                fetch_limit=1,
                min_score=1,
            ),
            RedditSubredditConfig(
                subreddit="MachineLearning",
                enabled=True,
                sort="hot",
                fetch_limit=1,
                min_score=1,
            ),
        ],
        users=[],
        fetch_comments=fetch_comments,
    )


def _listing_payload() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "data": {
            "children": [
                {
                    "kind": "t3",
                    "data": {
                        "id": "abc123",
                        "title": "Test post",
                        "is_self": True,
                        "subreddit": "LocalLLaMA",
                        "permalink": "/r/LocalLLaMA/comments/abc123/test_post/",
                        "author": "tester",
                        "created_utc": now.timestamp(),
                        "score": 42,
                        "upvote_ratio": 0.97,
                        "num_comments": 5,
                        "selftext": "post body",
                    },
                }
            ]
        }
    }


def _old_listing_html() -> str:
    timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return f"""
    <!doctype html>
    <div class="thing link self" data-fullname="t3_old123"
         data-subreddit="LocalLLaMA" data-author="old_author"
         data-score="42" data-timestamp="{timestamp_ms}"
         data-permalink="/r/LocalLLaMA/comments/old123/test_post/">
      <a class="title" href="/r/LocalLLaMA/comments/old123/test_post/">Old HTML post</a>
      <a class="comments">7 comments</a>
      <div class="expando"><div class="usertext-body"><div class="md">old body</div></div></div>
    </div>
    """


def _old_listing_html_for(subreddit: str, post_id: str) -> str:
    timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return f"""
    <!doctype html>
    <div class="thing link self" data-fullname="t3_{post_id}"
         data-subreddit="{subreddit}" data-author="old_author"
         data-score="42" data-timestamp="{timestamp_ms}"
         data-permalink="/r/{subreddit}/comments/{post_id}/test_post/">
      <a class="title" href="/r/{subreddit}/comments/{post_id}/test_post/">{subreddit} post</a>
      <a class="comments">7 comments</a>
      <div class="expando"><div class="usertext-body"><div class="md">old body</div></div></div>
    </div>
    """


def _old_comments_html() -> str:
    return """
    <!doctype html>
    <div class="comment" data-fullname="t1_c1" data-author="alice" data-score="10">
      <div class="usertext-body"><div class="md">first old comment</div></div>
    </div>
    <div class="comment" data-fullname="t1_c2" data-author="bob" data-score="2">
      <div class="usertext-body"><div class="md">second old comment</div></div>
    </div>
    """


def test_reddit_fetch_uses_browser_like_headers():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, text=_old_listing_html())

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    scraper = RedditScraper(_make_config(fetch_comments=0), client)

    asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1)))
    asyncio.run(client.aclose())

    assert len(requests) == 1
    assert requests[0].url.host == "old.reddit.com"
    assert requests[0].headers["user-agent"] == REDDIT_HEADERS["User-Agent"]
    assert requests[0].headers["accept-language"] == REDDIT_HEADERS["Accept-Language"]
    assert requests[0].headers["referer"] == REDDIT_HEADERS["Referer"]


def test_reddit_comment_403_degrades_to_post_without_comments():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "old.reddit.com":
            return httpx.Response(500, text="old reddit unavailable")
        if request.url.path.endswith("/hot.json"):
            return httpx.Response(200, json=_listing_payload())
        if "/comments/" in request.url.path:
            return httpx.Response(403, text="blocked")
        raise AssertionError(f"unexpected url: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    scraper = RedditScraper(_make_config(fetch_comments=3), client)

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1))).items
    asyncio.run(client.aclose())

    assert len(items) == 1
    assert items[0].title == "Test post"
    assert "Top Comments" not in (items[0].content or "")


def test_reddit_listing_uses_old_reddit_first():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "old.reddit.com" and request.url.path.endswith("/hot/"):
            return httpx.Response(200, text=_old_listing_html())
        raise AssertionError(f"unexpected url: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    scraper = RedditScraper(
        _make_config(fetch_comments=0, profile="subreddit-profile"), client
    )

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1))).items
    asyncio.run(client.aclose())

    assert [str(request.url.host) for request in requests] == ["old.reddit.com"]
    assert len(items) == 1
    assert items[0].title == "Old HTML post"
    assert items[0].content == "old body"
    assert items[0].author == "old_author"
    assert items[0].metadata["score"] == 42
    assert items[0].metadata["num_comments"] == 7
    assert items[0].profile == "subreddit-profile"


def test_reddit_listing_old_failure_falls_back_to_json_then_rss():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "old.reddit.com":
            return httpx.Response(500, text="old reddit unavailable")
        if request.url.path.endswith("/hot.json"):
            return httpx.Response(403, text="blocked")
        if request.url.path.endswith("/hot/.rss"):
            return httpx.Response(
                200,
                text="""
                <?xml version="1.0" encoding="UTF-8"?>
                <feed xmlns="http://www.w3.org/2005/Atom">
                  <entry>
                    <id>t3_rss123</id>
                    <title>RSS fallback post</title>
                    <author><name>rss_author</name></author>
                    <link href="https://www.reddit.com/r/LocalLLaMA/comments/rss123/test/" />
                    <updated>2030-01-01T00:00:00+00:00</updated>
                    <summary type="html">&lt;p&gt;RSS body&lt;/p&gt;</summary>
                  </entry>
                </feed>
                """,
            )
        if "/comments/" in request.url.path:
            return httpx.Response(403, text="blocked")
        raise AssertionError(f"unexpected url: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    scraper = RedditScraper(
        _make_config(fetch_comments=3, profile="rss-profile"), client
    )

    items = asyncio.run(scraper.fetch(datetime(2029, 12, 31, tzinfo=timezone.utc))).items
    asyncio.run(client.aclose())

    assert [request.url.path for request in requests] == [
        "/r/LocalLLaMA/hot/",
        "/r/LocalLLaMA/hot.json",
        "/r/LocalLLaMA/hot/.rss",
        "/r/LocalLLaMA/comments/rss123/",
        "/r/LocalLLaMA/comments/rss123.json",
    ]
    assert len(items) == 1
    assert items[0].title == "RSS fallback post"
    assert items[0].content == "RSS body"
    assert items[0].author == "rss_author"
    assert items[0].metadata["subreddit"] == "LocalLLaMA"
    assert items[0].metadata["fallback"] == "rss"
    assert items[0].profile == "rss-profile"


def test_reddit_user_profile_propagates() -> None:
    config = RedditConfig(
        enabled=True,
        subreddits=[],
        users=[RedditUserConfig(username="tester", profile="user-profile")],
        fetch_comments=0,
    )
    scraper = RedditScraper(config, AsyncMock())
    scraper._reddit_get = AsyncMock(return_value=_listing_payload())

    items = asyncio.run(
        scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1))
    ).items

    assert len(items) == 1
    assert items[0].profile == "user-profile"


def test_reddit_comments_use_old_reddit_first():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "old.reddit.com" and request.url.path.endswith("/hot/"):
            return httpx.Response(200, text=_old_listing_html())
        if request.url.host == "old.reddit.com" and "/comments/old123/" in request.url.path:
            return httpx.Response(200, text=_old_comments_html())
        raise AssertionError(f"unexpected url: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    scraper = RedditScraper(_make_config(fetch_comments=2), client)

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1))).items
    asyncio.run(client.aclose())

    assert [str(request.url.host) for request in requests] == [
        "old.reddit.com",
        "old.reddit.com",
    ]
    assert len(items) == 1
    content = items[0].content or ""
    assert "[alice (10 pts)]: first old comment" in content
    assert "[bob (2 pts)]: second old comment" in content


def test_reddit_subreddits_are_fetched_sequentially():
    requests = []
    local_done = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if "/r/LocalLLaMA/" in request.url.path:
            await asyncio.sleep(0)
            local_done.set()
            return httpx.Response(200, text=_old_listing_html_for("LocalLLaMA", "local123"))
        if "/r/MachineLearning/" in request.url.path:
            assert local_done.is_set()
            return httpx.Response(
                200, text=_old_listing_html_for("MachineLearning", "ml123")
            )
        raise AssertionError(f"unexpected url: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    scraper = RedditScraper(_make_two_subreddit_config(fetch_comments=0), client)

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1))).items
    asyncio.run(client.aclose())

    assert requests == ["/r/LocalLLaMA/hot/", "/r/MachineLearning/hot/"]
    assert [item.metadata["subreddit"] for item in items] == [
        "LocalLLaMA",
        "MachineLearning",
    ]


_RSS_FEED = """<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>t3_rss123</id><title>RSS post</title>
    <link href="https://www.reddit.com/r/LocalLLaMA/comments/rss123/test/" />
    <updated>2030-01-01T00:00:00+00:00</updated>
    <summary type="html">RSS body</summary>
  </entry>
</feed>"""


@pytest.mark.parametrize("mode", ["html", "json", "blocked", "timeout", "disabled", "cancelled"])
def test_rss_fallback_fetches_comments_best_effort(mode):
    requests = []

    def handler(request):
        requests.append(request)
        if "/comments/" in request.url.path:
            assert request.url.params["limit"] == "1"
            assert request.url.params["sort"] == "top"
            if mode == "cancelled":
                raise asyncio.CancelledError()
            if mode == "timeout":
                raise httpx.ReadTimeout("comments unavailable", request=request)
            if mode == "html":
                return httpx.Response(200, text=_old_comments_html())
            if mode == "json" and request.url.host == "www.reddit.com":
                return httpx.Response(200, json=[{}, {"data": {"children": [
                    {"kind": "t1", "data": {"author": "bob", "body": "lower comment", "score": 2}},
                    {"kind": "t1", "data": {"author": "alice", "body": "top comment", "score": 10}},
                ]}}])
            return httpx.Response(403)
        if request.url.path.endswith("/.rss"):
            return httpx.Response(200, text=_RSS_FEED)
        return httpx.Response(403)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            scraper = RedditScraper(_make_config(fetch_comments=0 if mode == "disabled" else 1), client)
            return await scraper.fetch(datetime(2029, 12, 31, tzinfo=timezone.utc))

    if mode == "cancelled":
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(run())
        return
    result = asyncio.run(run())
    assert result.status == "success"
    assert len(result.items) == 1
    item = result.items[0]
    assert item.content.startswith("RSS body")
    assert item.metadata["score"] is None
    assert item.metadata["num_comments"] is None
    assert item.metadata["fallback"] == "rss"
    if mode in {"html", "json"}:
        assert "--- Top Comments ---" in item.content
        assert "[alice (10 pts)]" in item.content
        assert "bob" not in item.content
    else:
        assert item.content == "RSS body"
    comment_requests = [r for r in requests if "/comments/" in r.url.path]
    assert len(comment_requests) == (0 if mode == "disabled" else 1 if mode == "html" else 2)


@pytest.mark.parametrize("entry_id,link,date,expected", [
    ("t3_rss123", "https://example.com/article", "2030-01-01", "rss123"),
    ("opaque-id", "https://www.reddit.com/r/LocalLLaMA/comments/url123/title/", "2030-01-01", "url123"),
    ("opaque-id", "https://www.reddit.com/r/LocalLLaMA/", "2030-01-01", None),
    ("opaque-id", "https://example.com/r/LocalLLaMA/comments/url123/", "2030-01-01", None),
    ("t3_rss123", "https://www.reddit.com/r/LocalLLaMA/comments/rss123/", "2029-01-01", None),
])
def test_rss_only_fetches_comments_for_recent_identifiable_posts(entry_id, link, date, expected):
    feed = _RSS_FEED.replace("t3_rss123", entry_id).replace(
        "https://www.reddit.com/r/LocalLLaMA/comments/rss123/test/", link,
    ).replace("2030-01-01", date)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, text=feed))) as client:
            config = _make_config()
            scraper = RedditScraper(config, client)
            scraper._fetch_comments = AsyncMock(return_value=[])
            items = await scraper._fetch_subreddit_rss(config.subreddits[0], datetime(2029, 12, 31, tzinfo=timezone.utc))
            if expected:
                scraper._fetch_comments.assert_awaited_once_with("LocalLLaMA", expected)
            else:
                scraper._fetch_comments.assert_not_awaited()
            assert len(items) == (0 if date == "2029-01-01" else 1)

    asyncio.run(run())
