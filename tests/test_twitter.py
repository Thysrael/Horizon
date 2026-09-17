"""Tests for TwitterScraper."""

import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx

from src.models import TwitterConfig
from src.scrapers.twitter import TwitterScraper
from src.scrapers.twitter_playwright import TwitterPlaywrightScraper


def _make_config(**kwargs) -> TwitterConfig:
    defaults = dict(
        enabled=True,
        users=["karpathy"],
        fetch_limit=3,
        actor_id="altimis~scweet",
        apify_token_env="APIFY_TOKEN",
    )
    defaults.update(kwargs)
    return TwitterConfig(**defaults)


def _tweet(
    tweet_id: str = "123456",
    screen_name: str = "karpathy",
    text: str = "Hello world",
    created_at: str = None,
    conversation_id: str = None,
    **extra,
) -> dict:
    if created_at is None:
        now = datetime.now(timezone.utc)
        created_at = now.strftime("%a %b %d %H:%M:%S +0000 %Y")
    return {
        "id_str": tweet_id,
        "conversation_id": conversation_id or tweet_id,
        "created_at": created_at,
        "full_text": text,
        "user": {"screen_name": screen_name, "name": screen_name.capitalize()},
        "favorite_count": 10,
        "retweet_count": 2,
        "reply_count": 1,
        **extra,
    }


def _reply_row(
    tweet_id: str = "999",
    handle: str = "someone",
    text: str = "Great point!",
    likes: int = 5,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": f"tweet-{tweet_id}",
        "handle": handle,
        "text": text,
        "favorite_count": likes,
        "reply_count": 0,
        "created_at": now.strftime("%a %b %d %H:%M:%S +0000 %Y"),
        "user": {"handle": handle, "name": handle},
    }


def _run_resp(run_id="run1", dataset_id="ds1"):
    return {"data": {"id": run_id, "defaultDatasetId": dataset_id}}


def _status_resp(status="SUCCEEDED"):
    return {"data": {"status": status}}


# ---------------------------------------------------------------------------
# Existing fetch tests
# ---------------------------------------------------------------------------

def test_disabled_returns_empty():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(enabled=False), client).fetch(
            datetime.now(timezone.utc)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_no_users_returns_empty():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(users=[], keywords=[]), client).fetch(
            datetime.now(timezone.utc)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_missing_token_returns_empty(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(), client).fetch(datetime.now(timezone.utc))
    )
    asyncio.run(client.aclose())
    assert result == []


def test_successful_fetch_returns_items(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    tweets = [_tweet("1"), _tweet("2", text="Another tweet")]

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=tweets)
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(profile="twitter-profile"), client).fetch(since)
    )
    asyncio.run(client.aclose())

    assert len(result) == 2
    assert result[0].source_type.value == "twitter"
    assert result[0].metadata["favorite_count"] == 10
    assert result[0].profile == "twitter-profile"


def test_playwright_parse_tweet_propagates_profile():
    scraper = TwitterPlaywrightScraper(
        _make_config(profile="playwright-profile"), http_client=None
    )
    item = scraper._parse_tweet(
        {
            "tweet_id": "123",
            "text": "Hello from Playwright",
            "datetime": datetime.now(timezone.utc).isoformat(),
        },
        "karpathy",
    )

    assert item is not None
    assert item.profile == "playwright-profile"


def test_metadata_keys_aligned_for_analyzer(monkeypatch):
    """Analyzer reads favorite_count/retweet_count/reply_count — verify they are set."""
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    tweets = [_tweet("42", **{"favorite_count": 99, "retweet_count": 7, "reply_count": 3})]

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=tweets)
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(TwitterScraper(_make_config(), client).fetch(since))
    asyncio.run(client.aclose())

    assert len(result) == 1
    meta = result[0].metadata
    assert meta["favorite_count"] == 99
    assert meta["retweet_count"] == 7
    assert meta["reply_count"] == 3
    assert meta["tweet_id"] == "42"
    assert "conversation_id" in meta


def test_filters_old_tweets(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc)
    old = (since - timedelta(hours=2)).strftime("%a %b %d %H:%M:%S +0000 %Y")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=[_tweet("1", created_at=old)])
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(TwitterScraper(_make_config(), client).fetch(since))
    asyncio.run(client.aclose())
    assert result == []


def test_run_failure_returns_empty(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp("FAILED"))
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(), client).fetch(
            datetime.now(timezone.utc) - timedelta(hours=1)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_start_run_http_error_returns_empty(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    transport = httpx.MockTransport(lambda r: httpx.Response(500, text="error"))
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(), client).fetch(
            datetime.now(timezone.utc) - timedelta(hours=1)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_no_results_item_skipped(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=[{"noResults": True}, _tweet("99")])
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(TwitterScraper(_make_config(), client).fetch(since))
    asyncio.run(client.aclose())

    assert len(result) == 1
    assert result[0].id == "twitter:tweet:99"


def test_iso_date_fallback(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    iso_tweet = _tweet("77")
    iso_tweet["created_at"] = datetime.now(timezone.utc).isoformat()

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=[iso_tweet])
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(TwitterScraper(_make_config(), client).fetch(since))
    asyncio.run(client.aclose())
    assert len(result) == 1


def test_url_constructed_when_missing(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    tweet = _tweet("55", screen_name="testuser")
    tweet.pop("url", None)

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=[tweet])
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(TwitterScraper(_make_config(), client).fetch(since))
    asyncio.run(client.aclose())

    assert len(result) == 1
    assert "testuser" in str(result[0].url)
    assert "55" in str(result[0].url)


# ---------------------------------------------------------------------------
# Keyword search fetch tests
# ---------------------------------------------------------------------------

def test_keywords_only_fetch_returns_items(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    tweets = [_tweet("k1", text="LLM news")]
    posted = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            posted["n"] += 1
            posted["payload"] = json.loads(request.content)
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=tweets)
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(users=[], keywords=["LLM"]), client).fetch(since)
    )
    asyncio.run(client.aclose())

    assert len(result) == 1
    assert result[0].id == "twitter:tweet:k1"
    assert posted["n"] == 1
    assert posted["payload"]["source_mode"] == "search"
    assert posted["payload"]["search_query"] == "LLM"
    assert posted["payload"]["search_sort"] == "Latest"
    assert posted["payload"]["max_items"] == 100


def test_missing_token_with_keywords_returns_empty(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(users=[], keywords=["AI"]), client).fetch(
            datetime.now(timezone.utc)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_empty_users_and_keywords_returns_empty():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(users=[], keywords=[]), client).fetch(
            datetime.now(timezone.utc)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_keyword_run_timed_out_returns_empty(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp("TIMED-OUT"))
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(users=[], keywords=["AI"]), client).fetch(
            datetime.now(timezone.utc) - timedelta(hours=1)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_keyword_failure_does_not_drop_user_tweets(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    user_tweets = [_tweet("u1", text="from timeline")]

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            body = json.loads(request.content)
            if body.get("source_mode") == "profiles":
                return httpx.Response(200, json=_run_resp("run-users", "ds-users"))
            return httpx.Response(200, json=_run_resp("run-kw", "ds-kw"))
        if request.url.path.endswith("/run-users"):
            return httpx.Response(200, json=_status_resp("SUCCEEDED"))
        if request.url.path.endswith("/run-kw"):
            return httpx.Response(200, json=_status_resp("FAILED"))
        if "/datasets/ds-users" in request.url.path:
            return httpx.Response(200, json=user_tweets)
        if "/datasets/ds-kw" in request.url.path:
            raise AssertionError("failed keyword run should not fetch dataset")
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(
            _make_config(users=["karpathy"], keywords=["AI"]), client
        ).fetch(since)
    )
    asyncio.run(client.aclose())

    assert len(result) == 1
    assert result[0].id == "twitter:tweet:u1"


def test_keyword_no_results_returns_empty(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            return httpx.Response(200, json=_run_resp())
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=[{"noResults": True}])
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(users=[], keywords=["nobody-uses-this"]), client).fetch(
            since
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_keyword_start_run_http_error_returns_empty(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    transport = httpx.MockTransport(lambda r: httpx.Response(500, text="error"))
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(_make_config(users=[], keywords=["AI"]), client).fetch(
            datetime.now(timezone.utc) - timedelta(hours=1)
        )
    )
    asyncio.run(client.aclose())
    assert result == []


def test_users_and_keywords_dedupe_by_id(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    shared = _tweet("same", text="seen twice")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            body = json.loads(request.content)
            if body.get("source_mode") == "profiles":
                return httpx.Response(200, json=_run_resp("run-users", "ds-users"))
            return httpx.Response(200, json=_run_resp("run-kw", "ds-kw"))
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=[shared])
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    result = asyncio.run(
        TwitterScraper(
            _make_config(users=["karpathy"], keywords=["LLM"]), client
        ).fetch(since)
    )
    asyncio.run(client.aclose())

    assert len(result) == 1
    assert result[0].id == "twitter:tweet:same"


def test_playwright_keywords_only_skips_without_users():
    scraper = TwitterPlaywrightScraper(
        _make_config(users=[], keywords=["LLM"], mode="playwright"),
        http_client=None,
    )
    result = asyncio.run(scraper.fetch(datetime.now(timezone.utc)))
    assert result == []


# ---------------------------------------------------------------------------
# Reply fetch tests
# ---------------------------------------------------------------------------

def test_fetch_replies_disabled_by_default():
    """fetch_reply_text defaults to False — verify config default."""
    cfg = TwitterConfig()
    assert cfg.fetch_reply_text is False


def test_fetch_replies_appends_top_comments(monkeypatch):
    """When fetch_reply_text=True, reply lines are appended under Top Comments."""
    monkeypatch.setenv("APIFY_TOKEN", "test_token")

    replies = [
        _reply_row("r1", "alice", "Interesting take!", likes=20),
        _reply_row("r2", "bob", "I disagree because...", likes=5),
        _reply_row("r3", "carol", "Great point!", likes=15),
        _reply_row("r4", "dave", "Low quality reply", likes=0),
    ]

    run_counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "/runs" in request.url.path and request.method == "POST":
            run_counter["n"] += 1
            ds = f"ds{run_counter['n']}"
            return httpx.Response(200, json=_run_resp(f"run{run_counter['n']}", ds))
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=_status_resp())
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=replies)
        raise AssertionError(f"Unexpected: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    cfg = _make_config(
        fetch_reply_text=True,
        max_replies_per_tweet=3,
        reply_min_likes=1,
    )
    scraper = TwitterScraper(cfg, client)

    from src.models import ContentItem, SourceType
    from datetime import datetime, timezone

    item = ContentItem(
        id="twitter:tweet:42",
        source_type=SourceType.TWITTER,
        title="@karpathy: test tweet",
        url="https://twitter.com/karpathy/status/42",
        content="test tweet body",
        author="Andrej Karpathy",
        published_at=datetime.now(timezone.utc),
        metadata={"tweet_id": "42", "conversation_id": "42"},
    )

    reply_lines = asyncio.run(scraper.fetch_replies_for_item(item))
    asyncio.run(client.aclose())

    # min_likes=1 filters out dave (0 likes); max 3 returned sorted by score
    assert len(reply_lines) == 3
    # alice (20 likes) should be first
    assert "alice" in reply_lines[0]
    assert "Interesting take!" in reply_lines[0]
    # dave (0 likes) filtered out
    assert not any("dave" in l for l in reply_lines)


def test_append_discussion_content_adds_marker():
    from src.models import ContentItem, SourceType

    item = ContentItem(
        id="twitter:tweet:1",
        source_type=SourceType.TWITTER,
        title="test",
        url="https://twitter.com/x/status/1",
        content="original text",
        author="x",
        published_at=datetime.now(timezone.utc),
        metadata={},
    )
    changed = TwitterScraper.append_discussion_content(item, ["[@alice | ❤️ 5 | 💬 1] reply text"])
    assert changed is True
    assert "--- Top Comments ---" in item.content
    assert "alice" in item.content


def test_append_discussion_content_empty_lines_no_change():
    from src.models import ContentItem, SourceType

    item = ContentItem(
        id="twitter:tweet:2",
        source_type=SourceType.TWITTER,
        title="test",
        url="https://twitter.com/x/status/2",
        content="original",
        author="x",
        published_at=datetime.now(timezone.utc),
        metadata={},
    )
    changed = TwitterScraper.append_discussion_content(item, [])
    assert changed is False
    assert item.content == "original"


def test_fetch_replies_no_conversation_id_returns_empty(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test_token")
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=[]))
    client = httpx.AsyncClient(transport=transport)
    cfg = _make_config(fetch_reply_text=True)
    scraper = TwitterScraper(cfg, client)

    from src.models import ContentItem, SourceType

    item = ContentItem(
        id="twitter:tweet:x",
        source_type=SourceType.TWITTER,
        title="test",
        url="https://twitter.com/x/status/x",
        content="body",
        author="x",
        published_at=datetime.now(timezone.utc),
        metadata={},  # no conversation_id
    )
    result = asyncio.run(scraper.fetch_replies_for_item(item))
    asyncio.run(client.aclose())
    assert result == []


