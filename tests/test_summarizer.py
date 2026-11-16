"""Unit tests for daily summary rendering."""

import asyncio
from datetime import datetime, timezone

from src.ai.summarizer import DailySummarizer
from src.models import (
    ArtifactSource,
    ClassificationResult,
    ContentAnalysis,
    ContentArtifact,
    ContentBlock,
    ContentItem,
    ProcessingResult,
    SourceType,
)


def _run_async(coro):
    return asyncio.run(coro)


def _make_item(idx: int) -> ContentItem:
    item = ContentItem(
        id=f"rss:item-{idx}",
        source_type=SourceType.RSS,
        title=f"Important Item {idx}",
        url=f"https://example.com/items/{idx}",
        content="content",
        author="tester",
        published_at=datetime(2026, 4, 25, 8, 0, tzinfo=timezone.utc),
        profile="tech-news",
        processing=ProcessingResult(
            classification=ClassificationResult(
                profile="tech-news", method="source_override"
            ),
            analysis=ContentAnalysis(
                score=8.0,
                reason="test",
                summary=f"Summary for item {idx}.",
                tags=["AI", "News"],
            ),
            artifacts={
                language: ContentArtifact(
                    language=language,
                    title=f"Important Item {idx}",
                    blocks=[
                        ContentBlock(
                            id="summary",
                            title="Summary",
                            content=f"Summary for item {idx}.",
                            primary=True,
                        )
                    ],
                )
                for language in ("en", "zh")
            },
        ),
    )
    return item


def test_generate_webhook_overview_lists_items_without_full_details():
    summarizer = DailySummarizer()
    items = [_make_item(1), _make_item(2)]

    result = summarizer.generate_webhook_overview(
        items,
        date="2026-04-25",
        total_fetched=10,
        language="en",
    )

    assert "Selected 2 important items from 10 fetched items" in result
    assert "1. [Important Item 1](https://example.com/items/1)" in result
    assert "2. [Important Item 2](https://example.com/items/2)" in result
    assert "Summary for item 1." not in result


def test_generate_webhook_item_renders_single_item_detail():
    summarizer = DailySummarizer()

    result = summarizer.generate_webhook_item(
        _make_item(1),
        language="en",
        index=1,
        total=2,
    )

    assert result.startswith("Item 1/2")
    assert "## [Important Item 1](https://example.com/items/1)" in result
    assert "Summary for item 1." in result
    assert "**Tags**: `#AI`, `#News`" in result


def test_generate_webhook_item_includes_discussion_link_when_distinct():
    summarizer = DailySummarizer()
    item = _make_item(1)
    item.metadata["discussion_url"] = "https://news.ycombinator.com/item?id=1"

    result = summarizer.generate_webhook_item(
        item,
        language="en",
        index=1,
        total=1,
    )

    assert "tester · Apr 25, 08:00 · [Discussion](https://news.ycombinator.com/item?id=1)" in result


def test_generate_webhook_item_omits_discussion_link_when_same_as_item_url():
    summarizer = DailySummarizer()
    item = _make_item(1)
    item.metadata["discussion_url"] = item.url

    result = summarizer.generate_webhook_item(
        item,
        language="en",
        index=1,
        total=1,
    )

    assert "[Discussion](https://example.com/items/1)" not in result


def test_generate_webhook_item_uses_localized_discussion_label():
    summarizer = DailySummarizer()
    item = _make_item(1)
    item.metadata["discussion_url"] = "https://www.reddit.com/r/python/comments/abc123/test/"

    result = summarizer.generate_webhook_item(
        item,
        language="zh",
        index=1,
        total=1,
    )

    assert "[社区讨论](https://www.reddit.com/r/python/comments/abc123/test/)" in result


def test_generate_summary_zh_uses_localized_selection_header_and_numeric_date():
    summarizer = DailySummarizer()
    item = _make_item(1)

    result = _run_async(
        summarizer.generate_summary(
            [item],
            date="2026-04-25",
            total_fetched=10,
            language="zh",
        )
    )

    assert "> 从 10 条内容中筛选出 1 条重要资讯。" in result
    assert "rss · tester · 4月25日 08:00" in result
    assert "From 10 items" not in result
    assert "Apr 25, 08:00" not in result


def test_generate_summary_groups_items_by_profile_with_heading_hierarchy():
    news = _make_item(1)
    blog = _make_item(2)
    blog.profile = "tech-blog"
    blog.processing.classification.profile = "tech-blog"
    summarizer = DailySummarizer(
        profile_names={
            "tech-news": {"default": "Technology News", "zh": "科技新闻"},
            "tech-blog": {"default": "Technology Blog", "zh": "科技博客"},
        }
    )

    result = _run_async(
        summarizer.generate_summary(
            [news, blog],
            date="2026-04-25",
            total_fetched=2,
            language="en",
        )
    )

    assert result.count("# Horizon Daily") == 1
    assert "## Technology News" in result
    assert "## Technology Blog" in result
    assert "### [Important Item 1]" in result
    assert "### [Important Item 2]" in result


def test_generate_summary_uses_configured_profile_order():
    finance = _make_item(1)
    finance.profile = "finance-news"
    finance.processing.classification.profile = "finance-news"
    blog = _make_item(2)
    blog.profile = "tech-blog"
    blog.processing.classification.profile = "tech-blog"
    news = _make_item(3)
    summarizer = DailySummarizer(
        profile_names={
            "tech-news": {"default": "Technology News"},
            "tech-blog": {"default": "Technology Blog"},
            "finance-news": {"default": "Financial News"},
        },
        profile_order=["tech-news", "tech-blog", "finance-news"],
    )

    result = _run_async(
        summarizer.generate_summary(
            [finance, blog, news],
            date="2026-04-25",
            total_fetched=3,
            language="en",
        )
    )

    assert result.index("## Technology News") < result.index("## Technology Blog")
    assert result.index("## Technology Blog") < result.index("## Financial News")


def test_generate_summary_renders_primary_block_before_source_without_heading():
    item = _make_item(1)
    item.processing.artifacts["en"] = ContentArtifact(
        language="en",
        title="Important Item 1",
        blocks=[
            ContentBlock(
                id="summary",
                title="Summary",
                content="Primary explanation.",
                primary=True,
            ),
            ContentBlock(
                id="background",
                title="Background",
                content="Supporting context.",
            ),
        ],
    )

    result = _run_async(
        DailySummarizer().generate_summary(
            [item],
            date="2026-04-25",
            total_fetched=1,
            language="en",
        )
    )

    assert "#### Summary" not in result
    assert result.index("Primary explanation.") < result.index(
        "rss · tester · Apr 25, 08:00"
    )
    assert result.index("rss · tester · Apr 25, 08:00") < result.index(
        "**「Background」** Supporting context."
    )


def test_generate_summary_renders_non_primary_blog_sections_after_source():
    item = _make_item(1)
    item.profile = "tech-blog"
    item.processing.classification.profile = "tech-blog"
    item.processing.artifacts["en"] = ContentArtifact(
        language="en",
        title="A technical article",
        blocks=[
            ContentBlock(
                id="background",
                title="Background",
                content="The original constraints.",
            ),
            ContentBlock(
                id="solution",
                title="Solution",
                content="The implementation and evidence.",
            ),
            ContentBlock(
                id="takeaway",
                title="Takeaway",
                content="The durable lesson.",
            ),
        ],
    )

    result = _run_async(
        DailySummarizer().generate_summary(
            [item],
            date="2026-04-25",
            total_fetched=1,
            language="en",
        )
    )

    source_index = result.index("rss · tester · Apr 25, 08:00")
    context_index = result.index("**「Background」** The original constraints.")
    solution_index = result.index("**「Solution」** The implementation and evidence.")
    takeaway_index = result.index("**「Takeaway」** The durable lesson.")
    assert source_index < context_index < solution_index < takeaway_index
    assert "#### Background" not in result


def test_generate_webhook_item_normalizes_existing_zh_artifact_to_simplified():
    item = _make_item(1)
    item.processing.artifacts["zh"] = ContentArtifact(
        language="zh",
        title="代理工作流更新",
        blocks=[
            ContentBlock(
                id="background",
                title="背景",
                content="社群關注這項更新，並分享實際用量數據。",
            )
        ],
    )

    result = DailySummarizer().generate_webhook_item(
        item,
        language="zh",
        index=1,
        total=1,
    )

    assert "代理工作流更新" in result
    assert "**「背景」** 社群关注这项更新，并分享实际用量数据。" in result
    assert "關注" not in result


def test_generate_summary_renumbers_interleaved_profiles_and_localizes_headings():
    first_news = _make_item(1)
    blog = _make_item(2)
    second_news = _make_item(3)
    blog.profile = "tech-blog"
    blog.processing.classification.profile = "tech-blog"
    summarizer = DailySummarizer(
        profile_names={
            "tech-news": {"default": "Technology News", "zh": "科技新闻"},
            "tech-blog": {"default": "Technology Blog", "zh": "科技博客"},
        }
    )

    result = _run_async(
        summarizer.generate_summary(
            [first_news, blog, second_news],
            date="2026-04-25",
            total_fetched=3,
            language="zh",
        )
    )

    assert "## 科技新闻" in result
    assert "## 科技博客" in result
    assert "1. [Important Item 1](#item-tech-news-1)" in result
    assert "2. [Important Item 3](#item-tech-news-2)" in result
    assert "1. [Important Item 2](#item-tech-blog-1)" in result
    assert result.index("2. [Important Item 3]") < result.index("1. [Important Item 2]")
    assert '<a id="item-tech-news-1"></a>' in result
    assert '<a id="item-tech-blog-1"></a>' in result


def test_generate_empty_summary_zh_uses_localized_analyzed_line():
    summarizer = DailySummarizer()

    result = _run_async(
        summarizer.generate_summary(
            [],
            date="2026-04-25",
            total_fetched=10,
            language="zh",
        )
    )

    assert "> 已分析 10 条内容，但没有达到重要性阈值的条目。" in result
    assert "Analyzed 10 items" not in result


def test_generate_summary_escapes_untrusted_text_in_all_output_contexts():
    summarizer = DailySummarizer()
    item = _make_item(1)
    item.title = '<script>alert("title")</script> [click](javascript:alert(1))'
    item.processing.analysis.summary = '<img src=x onerror="alert(1)"> **summary**'
    item.author = '<svg onload="alert(1)">'
    item.processing.analysis.tags = ['tag`](javascript:alert(1))']
    item.processing.artifacts["en"] = ContentArtifact(
        language="en",
        title=item.title,
        blocks=[
            ContentBlock(
                id="summary",
                title="Summary",
                content='<img src=x onerror="alert(1)"> **summary**',
                primary=True,
            ),
            ContentBlock(
                id="background",
                title="Background",
                content='<iframe src="data:text/html,bad"></iframe>',
            ),
            ContentBlock(
                id="community_discussion",
                title="Discussion",
                content="[bad](data:text/html,bad)",
            ),
        ],
        sources=[
            ArtifactSource(
                id="ref-1",
                title='<img src=x onerror="alert(1)">',
                url="https://example.com/ref",
            )
        ],
    )
    item.metadata.update(
        {
            "feed_name": '<b onclick="alert(1)">feed</b>',
        }
    )

    result = _run_async(summarizer.generate_summary([item], "2026-04-25", 1))

    assert "<script>" not in result
    assert "<img src=x" not in result
    assert "<iframe" not in result
    assert "<b onclick" not in result
    assert "](javascript:" not in result
    assert "](data:text/html" not in result
    assert "&lt;script&gt;" in result
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in result


def test_generate_summary_rejects_unsafe_urls_and_quote_injection():
    summarizer = DailySummarizer()
    item = _make_item(1)
    item.metadata["discussion_url"] = 'javascript:alert("discussion")'
    item.processing.artifacts["en"].sources = [
        ArtifactSource(
            id="quoted",
            title='Quoted "><script>alert(1)</script>',
            url='https://example.com/\" onmouseover=\"alert(1)',
        ),
        ArtifactSource(id="js", title="JavaScript", url="javascript:alert(1)"),
        ArtifactSource(
            id="data",
            title="Data",
            url="data:text/html,<script>alert(1)</script>",
        ),
    ]

    result = _run_async(summarizer.generate_summary([item], "2026-04-25", 1))

    assert 'href="https://example.com/%22%20onmouseover=%22alert%281%29"' in result
    assert '<li>JavaScript</li>' in result
    assert '<li>Data</li>' in result
    assert 'href="javascript:' not in result
    assert 'href="data:' not in result
    assert '<script>' not in result


def test_generate_summary_preserves_normal_http_links():
    summarizer = DailySummarizer()
    item = _make_item(1)
    item.metadata["discussion_url"] = "https://example.com/discuss?id=1#comments"
    item.processing.artifacts["en"].sources = [
        ArtifactSource(
            id="useful",
            title="Useful reference",
            url="https://docs.example.com/path?q=one&lang=en",
        )
    ]

    result = _run_async(summarizer.generate_summary([item], "2026-04-25", 1))

    assert "[Important Item 1](https://example.com/items/1)" in result
    assert "[Discussion](https://example.com/discuss?id=1#comments)" in result
    assert 'href="https://docs.example.com/path?q=one&amp;lang=en"' in result


def test_summary_discloses_rss_fallback_without_claiming_full_article():
    item = _make_item(1)
    item.metadata['content_origin'] = 'rss_fallback'
    text = _run_async(DailySummarizer().generate_summary([item], '2026-10-27', 1, language='zh'))
    assert 'RSS 内容（网页获取失败）' in text
    assert '网页正文提取' not in text
    item.metadata['content_origin'] = 'web'
    text = _run_async(DailySummarizer().generate_summary([item], '2026-10-27', 1, language='zh'))
    assert '网页正文提取' in text
    assert '网页获取失败' not in text
