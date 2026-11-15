import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from src.models import RSSSourceConfig
from src.scrapers.rss import RSSScraper


@pytest.mark.parametrize(
    ("encoding", "title", "content_type", "declaration"),
    [
        ("iso-8859-1", "Café", "application/rss+xml", True),
        ("gb18030", "中文新闻", "application/rss+xml", True),
        ("iso-8859-1", "Café", "application/rss+xml; charset=iso-8859-1", False),
        ("utf-8", "中文 Café", "application/rss+xml", True),
    ],
)
def test_fetch_respects_feed_encoding(
    encoding: str, title: str, content_type: str, declaration: bool
) -> None:
    xml = f'<?xml version="1.0" encoding="{encoding}"?>' if declaration else ""
    feed = f"""{xml}<rss version="2.0"><channel><title>News</title>
<item><guid>entry-1</guid><title>{title}</title>
<link>https://example.com/article</link>
<pubDate>Mon, 02 Nov 2026 09:00:00 GMT</pubDate>
<description>{title}</description></item></channel></rss>"""

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, content=feed.encode(encoding), headers={"Content-Type": content_type}
            )
        )) as client:
            source = RSSSourceConfig(name="News", url="https://example.com/feed")
            return await RSSScraper([source], client).fetch(
                datetime(2026, 11, 2, tzinfo=timezone.utc)
            )

    result = asyncio.run(run())
    assert result.status == "success"
    assert len(result.items) == 1
    assert result.items[0].title == title
    assert result.items[0].content == title
