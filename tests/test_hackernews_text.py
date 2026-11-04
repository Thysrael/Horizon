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
    assert "<5ms.\n\nMore evidence." in item.content
    assert "It's not confirmed" in item.content
    assert "<p>" not in item.content
    assert "&amp;" not in item.content
    assert "&#39;" not in item.content


def test_hackernews_text_preserves_code_indentation_and_line_breaks():
    from src.scrapers.hackernews import _html_text
    text = _html_text("<p>Example<br>next line</p><pre>def f():\n    return 1</pre>")
    assert text == "Example\nnext line\n\ndef f():\n    return 1"


def test_leading_preformatted_code_indentation_is_preserved():
    from src.scrapers.hackernews import _html_text
    assert _html_text("<pre><code>    indented\n    second</code></pre>") == "    indented\n    second"
