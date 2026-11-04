from unittest.mock import AsyncMock

from src.models import HackerNewsConfig
from src.scrapers.hackernews import HackerNewsScraper


def test_hackernews_html_is_decoded_before_becoming_source_evidence():
    scraper = HackerNewsScraper(HackerNewsConfig(), AsyncMock())
    item = scraper._parse_story({
        "id": 42, "time": 1793534400, "title": "Ask HN: AT&amp;T &lt;5ms?",
        "text": "<p>AT&amp;T announced &lt;5ms.</p><p>More evidence.</p>",
    }, [{"by": "reader", "text": "<p>It&#39;s <b>not</b> confirmed&nbsp;yet.</p>"}])
    assert item.title == "Ask HN: AT&T <5ms?"
    assert "AT&T announced <5ms." in item.content
    assert "More evidence." in item.content
    assert "It's not confirmed" in item.content
    assert "<p>" not in item.content
    assert "&amp;" not in item.content
    assert "&#39;" not in item.content
