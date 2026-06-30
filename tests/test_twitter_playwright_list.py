from datetime import datetime, timezone

from src.models import TwitterConfig
from src.scrapers.twitter_playwright import TwitterPlaywrightScraper


def test_twitter_config_accepts_list_id_and_default_category():
    cfg = TwitterConfig(mode="playwright", list_id="123", category="ai-tools")

    assert cfg.list_id == "123"
    assert cfg.category == "ai-tools"


def test_playwright_list_tweets_use_real_author_and_configured_category():
    cfg = TwitterConfig(mode="playwright", list_id="123", category="ai-tools")
    scraper = TwitterPlaywrightScraper(cfg)

    item = scraper._parse_tweet(
        {
            "tweet_id": "42",
            "text": "AI agent tool release",
            "datetime": datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc).isoformat(),
            "username": "real_author",
        },
        "list",
    )

    assert item is not None
    assert item.author == "real_author"
    assert str(item.url) == "https://x.com/real_author/status/42"
    assert item.metadata["category"] == "ai-tools"
    assert item.metadata["list_id"] == "123"
