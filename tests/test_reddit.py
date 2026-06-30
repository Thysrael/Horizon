import asyncio
from datetime import datetime, timedelta, timezone

import httpx

from src.models import RedditConfig, RedditSubredditConfig
from src.scrapers.reddit import REDDIT_HEADERS, RedditScraper


def _make_config(fetch_comments: int = 1) -> RedditConfig:
    return RedditConfig(
        enabled=True,
        subreddits=[
            RedditSubredditConfig(
                subreddit="LocalLLaMA",
                enabled=True,
                sort="hot",
                fetch_limit=1,
                min_score=1,
                category="ai-tools",
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

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1)))
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
    scraper = RedditScraper(_make_config(fetch_comments=0), client)

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1)))
    asyncio.run(client.aclose())

    assert [str(request.url.host) for request in requests] == ["old.reddit.com"]
    assert len(items) == 1
    assert items[0].title == "Old HTML post"
    assert items[0].content == "old body"
    assert items[0].author == "old_author"
    assert items[0].metadata["score"] == 42
    assert items[0].metadata["num_comments"] == 7
    assert items[0].metadata["category"] == "ai-tools"


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
        raise AssertionError(f"unexpected url: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    scraper = RedditScraper(_make_config(fetch_comments=3), client)

    items = asyncio.run(scraper.fetch(datetime(2029, 12, 31, tzinfo=timezone.utc)))
    asyncio.run(client.aclose())

    assert [request.url.path for request in requests] == [
        "/r/LocalLLaMA/hot/",
        "/r/LocalLLaMA/hot.json",
        "/r/LocalLLaMA/hot/.rss",
    ]
    assert len(items) == 1
    assert items[0].title == "RSS fallback post"
    assert items[0].content == "RSS body"
    assert items[0].author == "rss_author"
    assert items[0].metadata["subreddit"] == "LocalLLaMA"
    assert items[0].metadata["fallback"] == "rss"
    assert items[0].metadata["category"] == "ai-tools"


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

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1)))
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

    items = asyncio.run(scraper.fetch(datetime.now(timezone.utc) - timedelta(hours=1)))
    asyncio.run(client.aclose())

    assert requests == ["/r/LocalLLaMA/hot/", "/r/MachineLearning/hot/"]
    assert [item.metadata["subreddit"] for item in items] == [
        "LocalLLaMA",
        "MachineLearning",
    ]
