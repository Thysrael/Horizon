"""Tests for the visual-extraction sub-step wired into ContentEnricher
(src/ai/enricher.py): the gate matrix (_resolve_visual_extraction), the
render+vision sub-step (_maybe_visual_extract), and enrich_batch's lazy
VisualRenderer construction/teardown.

Fully mocked: no real Playwright browser, no live AI/vision calls. The AI
client and visual renderer are both simple fake objects with async methods
recording their calls.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import List, Optional
from unittest.mock import AsyncMock, patch

from src.ai.enricher import ContentEnricher
from src.models import (
    ContentItem,
    GDELTConfig,
    GoogleNewsConfig,
    RSSSourceConfig,
    SourceType,
    SourcesConfig,
    VisualExtractionConfig,
)

PNG_BYTES = b"fake-screenshot-bytes"


def _valid_enrichment_json() -> str:
    """A minimal but well-formed CONTENT_ENRICHMENT_USER-shaped JSON response."""
    return json.dumps(
        {
            "title_en": "Title",
            "title_zh": "标题",
            "whats_new_en": "Something new happened.",
            "whats_new_zh": "发生了新事情。",
            "why_it_matters_en": "It matters because reasons.",
            "why_it_matters_zh": "这很重要。",
            "key_details_en": "Some key detail.",
            "key_details_zh": "一些关键细节。",
            "background_en": "",
            "background_zh": "",
            "community_discussion_en": "",
            "community_discussion_zh": "",
            "sources": [],
        }
    )


class _FakeAIClient:
    """Fake AIClient recording calls to complete() and complete_vision()."""

    def __init__(
        self,
        complete_result: str = None,
        vision_result: Optional[str] = None,
        vision_exc: Optional[Exception] = None,
    ):
        self.complete_result = complete_result or _valid_enrichment_json()
        self.vision_result = vision_result
        self.vision_exc = vision_exc
        self.complete_calls: List[tuple] = []
        self.vision_calls: List[tuple] = []
        self.config = SimpleNamespace(enrichment_concurrency=1)

    async def complete(self, system, user, temperature=None, max_tokens=None):
        self.complete_calls.append((system, user))
        return self.complete_result

    async def complete_vision(
        self,
        system,
        user,
        image_data,
        image_media_type="image/png",
        temperature=None,
        max_tokens=None,
    ):
        self.vision_calls.append((system, user, image_data, image_media_type))
        if self.vision_exc is not None:
            raise self.vision_exc
        return self.vision_result


class _FakeRenderer:
    """Fake VisualRenderer-like object recording render() calls."""

    def __init__(self, render_result: Optional[bytes] = PNG_BYTES, render_exc: Optional[Exception] = None):
        self.render_result = render_result
        self.render_exc = render_exc
        self.render_calls: List[str] = []

    async def render(self, url: str) -> Optional[bytes]:
        self.render_calls.append(url)
        if self.render_exc is not None:
            raise self.render_exc
        return self.render_result


def _rss_item(feed_name: str = "TestFeed", content: str = "Thin RSS snippet.") -> ContentItem:
    return ContentItem(
        id="rss:test:1",
        source_type=SourceType.RSS,
        title="RSS Article Title",
        url="https://example.com/article",
        content=content,
        published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        metadata={"feed_name": feed_name},
    )


def _gdelt_item(content: str = "Thin GDELT snippet.") -> ContentItem:
    return ContentItem(
        id="gdelt:test:1",
        source_type=SourceType.GDELT,
        title="GDELT Article Title",
        url="https://news.example.com/gdelt-story",
        content=content,
        published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def _google_news_item(content: str = "Thin Google News snippet.") -> ContentItem:
    return ContentItem(
        id="google_news:test:1",
        source_type=SourceType.GOOGLE_NEWS,
        title="Google News Article Title",
        url="https://news.example.com/gnews-story",
        content=content,
        published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def _github_item(content: str = "Github release notes.") -> ContentItem:
    return ContentItem(
        id="github:test:1",
        source_type=SourceType.GITHUB,
        title="Github Release",
        url="https://github.com/example/repo/releases/tag/v1",
        content=content,
        published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )


def _sources_config_with_rss_enabled(feed_name: str = "TestFeed", enabled: bool = True) -> SourcesConfig:
    return SourcesConfig(
        rss=[
            RSSSourceConfig(
                name=feed_name,
                url="https://example.com/feed.xml",
                visual_extraction=VisualExtractionConfig(enabled=enabled),
            )
        ]
    )


def _assert_normal_enrichment_happened(item: ContentItem) -> None:
    """Assert the rest of _enrich_item ran to completion (existing behavior)."""
    assert item.metadata.get("detailed_summary_en"), "expected normal enrichment fields to be set"
    assert item.metadata.get("detailed_summary") == item.metadata.get("detailed_summary_en")


class TestResolveVisualExtractionGateMatrix:
    """Directly exercises _resolve_visual_extraction across the full gate matrix."""

    def test_rss_matching_feed_enabled_resolves_config(self):
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)
        item = _rss_item(feed_name="TestFeed")

        resolved = enricher._resolve_visual_extraction(item)

        assert resolved is not None
        assert resolved.enabled is True

    def test_rss_disabled_by_default_resolves_none(self):
        # Default RSSSourceConfig.visual_extraction.enabled is False.
        sources_config = SourcesConfig(
            rss=[RSSSourceConfig(name="TestFeed", url="https://example.com/feed.xml")]
        )
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)
        item = _rss_item(feed_name="TestFeed")

        assert enricher._resolve_visual_extraction(item) is None

    def test_rss_feed_name_mismatch_resolves_none(self):
        sources_config = _sources_config_with_rss_enabled("ConfiguredFeed", enabled=True)
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)
        item = _rss_item(feed_name="SomeOtherFeed")

        assert enricher._resolve_visual_extraction(item) is None

    def test_sources_config_none_resolves_none(self):
        enricher = ContentEnricher(_FakeAIClient(), sources_config=None)
        item = _rss_item(feed_name="TestFeed")

        assert enricher._resolve_visual_extraction(item) is None

    def test_non_eligible_source_type_resolves_none_even_if_enabled_elsewhere(self):
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        sources_config.gdelt = GDELTConfig(visual_extraction=VisualExtractionConfig(enabled=True))
        sources_config.google_news = GoogleNewsConfig(visual_extraction=VisualExtractionConfig(enabled=True))
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)

        for item in (_github_item(),):
            assert enricher._resolve_visual_extraction(item) is None

    def test_gdelt_enabled_when_configured(self):
        sources_config = SourcesConfig(gdelt=GDELTConfig(visual_extraction=VisualExtractionConfig(enabled=True)))
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)
        item = _gdelt_item()

        resolved = enricher._resolve_visual_extraction(item)
        assert resolved is not None
        assert resolved.enabled is True

    def test_gdelt_none_by_default_resolves_none(self):
        sources_config = SourcesConfig()  # gdelt defaults to None
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)
        item = _gdelt_item()

        assert sources_config.gdelt is None
        assert enricher._resolve_visual_extraction(item) is None

    def test_google_news_enabled_when_configured(self):
        sources_config = SourcesConfig(
            google_news=GoogleNewsConfig(visual_extraction=VisualExtractionConfig(enabled=True))
        )
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)
        item = _google_news_item()

        resolved = enricher._resolve_visual_extraction(item)
        assert resolved is not None

    def test_google_news_none_by_default_resolves_none(self):
        sources_config = SourcesConfig()  # google_news defaults to None
        enricher = ContentEnricher(_FakeAIClient(), sources_config=sources_config)
        item = _google_news_item()

        assert sources_config.google_news is None
        assert enricher._resolve_visual_extraction(item) is None


class TestMaybeVisualExtractSuccessPaths:
    def test_differs_meaningfully_true_sets_metadata_and_returns_extracted_text(self):
        ai_client = _FakeAIClient(
            vision_result=json.dumps(
                {"differs_meaningfully": True, "extracted_content": "The real, full article text..."}
            )
        )
        renderer = _FakeRenderer(render_result=PNG_BYTES)
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        result = asyncio.run(enricher._maybe_visual_extract(item, "Thin snippet."))

        assert result == "The real, full article text..."
        assert item.metadata["visual_extracted_content"] == "The real, full article text..."
        assert renderer.render_calls == ["https://example.com/article"]
        assert len(ai_client.vision_calls) == 1

    def test_differs_meaningfully_false_leaves_metadata_and_content_unchanged(self):
        ai_client = _FakeAIClient(
            vision_result=json.dumps({"differs_meaningfully": False, "extracted_content": ""})
        )
        renderer = _FakeRenderer(render_result=PNG_BYTES)
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        result = asyncio.run(enricher._maybe_visual_extract(item, "Thin snippet."))

        assert result == "Thin snippet."
        assert "visual_extracted_content" not in item.metadata
        assert len(ai_client.vision_calls) == 1

    def test_full_enrich_item_completes_and_reflects_extracted_content(self):
        ai_client = _FakeAIClient(
            vision_result=json.dumps(
                {"differs_meaningfully": True, "extracted_content": "Real article body."}
            )
        )
        renderer = _FakeRenderer(render_result=PNG_BYTES)
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        asyncio.run(enricher._enrich_item(item))

        assert item.metadata["visual_extracted_content"] == "Real article body."
        _assert_normal_enrichment_happened(item)
        assert len(renderer.render_calls) == 1
        assert len(ai_client.vision_calls) == 1


class TestMaybeVisualExtractDisabledPath:
    def test_toggle_disabled_never_calls_render_or_vision(self):
        ai_client = _FakeAIClient()
        renderer = _FakeRenderer()
        # visual_extraction.enabled defaults to False
        sources_config = SourcesConfig(
            rss=[RSSSourceConfig(name="TestFeed", url="https://example.com/feed.xml")]
        )
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        asyncio.run(enricher._enrich_item(item))

        assert renderer.render_calls == []
        assert ai_client.vision_calls == []
        assert "visual_extracted_content" not in item.metadata
        _assert_normal_enrichment_happened(item)

    def test_sources_config_none_default_pattern_fully_unaffected(self):
        """ContentEnricher(ai_client) — today's existing call pattern."""
        ai_client = _FakeAIClient()
        enricher = ContentEnricher(ai_client)  # no sources_config, no visual_renderer
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        asyncio.run(enricher._enrich_item(item))

        assert ai_client.vision_calls == []
        assert "visual_extracted_content" not in item.metadata
        _assert_normal_enrichment_happened(item)

    def test_feed_name_mismatch_treated_as_disabled_no_crash(self):
        ai_client = _FakeAIClient()
        renderer = _FakeRenderer()
        sources_config = _sources_config_with_rss_enabled("ConfiguredFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="UnrelatedFeed", content="Thin snippet.")

        asyncio.run(enricher._enrich_item(item))

        assert renderer.render_calls == []
        assert ai_client.vision_calls == []
        _assert_normal_enrichment_happened(item)

    def test_non_eligible_source_type_is_complete_noop(self):
        ai_client = _FakeAIClient()
        renderer = _FakeRenderer()
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        sources_config.gdelt = GDELTConfig(visual_extraction=VisualExtractionConfig(enabled=True))
        sources_config.google_news = GoogleNewsConfig(visual_extraction=VisualExtractionConfig(enabled=True))
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _github_item()

        asyncio.run(enricher._enrich_item(item))

        assert renderer.render_calls == []
        assert ai_client.vision_calls == []
        _assert_normal_enrichment_happened(item)


class TestGracefulDegradation:
    """Every failure mode must fall back cleanly to the original content_text
    and let _enrich_item / enrich_batch complete without raising."""

    def test_render_returns_none_falls_back_cleanly(self):
        ai_client = _FakeAIClient()
        renderer = _FakeRenderer(render_result=None)
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        asyncio.run(enricher._enrich_item(item))

        assert renderer.render_calls == ["https://example.com/article"]
        assert ai_client.vision_calls == []  # never reached — render short-circuited
        assert "visual_extracted_content" not in item.metadata
        _assert_normal_enrichment_happened(item)

    def test_render_raises_exception_falls_back_cleanly(self):
        ai_client = _FakeAIClient()
        renderer = _FakeRenderer(render_exc=RuntimeError("playwright exploded"))
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        # Must not raise.
        asyncio.run(enricher._enrich_item(item))

        assert "visual_extracted_content" not in item.metadata
        _assert_normal_enrichment_happened(item)

    def test_complete_vision_not_implemented_error_falls_back_cleanly(self):
        ai_client = _FakeAIClient(vision_exc=NotImplementedError("AzureOpenAIClient does not support vision"))
        renderer = _FakeRenderer(render_result=PNG_BYTES)
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        asyncio.run(enricher._enrich_item(item))

        assert "visual_extracted_content" not in item.metadata
        _assert_normal_enrichment_happened(item)

    def test_complete_vision_malformed_json_falls_back_cleanly(self):
        ai_client = _FakeAIClient(vision_result="this is not json at all, sorry")
        renderer = _FakeRenderer(render_result=PNG_BYTES)
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Thin snippet.")

        asyncio.run(enricher._enrich_item(item))

        assert "visual_extracted_content" not in item.metadata
        _assert_normal_enrichment_happened(item)

    def test_maybe_visual_extract_swallows_any_exception_directly(self):
        """Direct unit check that _maybe_visual_extract's try/except covers
        render() raising, independent of the full _enrich_item flow."""
        ai_client = _FakeAIClient()
        renderer = _FakeRenderer(render_exc=ValueError("boom"))
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        item = _rss_item(feed_name="TestFeed", content="Original snippet.")

        result = asyncio.run(enricher._maybe_visual_extract(item, "Original snippet."))

        assert result == "Original snippet."


class TestEnrichBatchLazyRendererConstruction:
    def test_constructs_and_enters_renderer_when_batch_needs_it(self):
        class _FakeVisualRendererCM:
            instances: List["_FakeVisualRendererCM"] = []

            def __init__(self, timeout_ms=15000, **kwargs):
                self.timeout_ms = timeout_ms
                self.entered = False
                self.exited = False
                self.render = AsyncMock(return_value=PNG_BYTES)
                type(self).instances.append(self)

            async def __aenter__(self):
                self.entered = True
                return self

            async def __aexit__(self, exc_type, exc, tb):
                self.exited = True

        _FakeVisualRendererCM.instances = []

        ai_client = _FakeAIClient(
            vision_result=json.dumps({"differs_meaningfully": False, "extracted_content": ""})
        )
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config)  # no injected renderer
        items = [_rss_item(feed_name="TestFeed")]

        with patch("src.ai.visual_renderer.VisualRenderer", _FakeVisualRendererCM):
            asyncio.run(enricher.enrich_batch(items))

        assert len(_FakeVisualRendererCM.instances) == 1
        instance = _FakeVisualRendererCM.instances[0]
        assert instance.entered is True
        assert instance.exited is True
        # Renderer reset to None after the batch tears it down.
        assert enricher._visual_renderer is None
        instance.render.assert_awaited_once()

    def test_uses_max_timeout_across_items_needing_extraction(self):
        class _FakeVisualRendererCM:
            instances: List["_FakeVisualRendererCM"] = []

            def __init__(self, timeout_ms=15000, **kwargs):
                self.timeout_ms = timeout_ms
                self.render = AsyncMock(return_value=None)
                type(self).instances.append(self)

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                pass

        _FakeVisualRendererCM.instances = []

        ai_client = _FakeAIClient()
        sources_config = SourcesConfig(
            rss=[
                RSSSourceConfig(
                    name="FastFeed",
                    url="https://example.com/fast.xml",
                    visual_extraction=VisualExtractionConfig(enabled=True, timeout_ms=5000),
                ),
                RSSSourceConfig(
                    name="SlowFeed",
                    url="https://example.com/slow.xml",
                    visual_extraction=VisualExtractionConfig(enabled=True, timeout_ms=20000),
                ),
            ]
        )
        enricher = ContentEnricher(ai_client, sources_config=sources_config)
        items = [
            _rss_item(feed_name="FastFeed"),
            _rss_item(feed_name="SlowFeed"),
        ]
        items[1].id = "rss:test:2"

        with patch("src.ai.visual_renderer.VisualRenderer", _FakeVisualRendererCM):
            asyncio.run(enricher.enrich_batch(items))

        assert _FakeVisualRendererCM.instances[0].timeout_ms == 20000

    def test_never_constructs_renderer_when_no_item_needs_it(self):
        class _ExplodingVisualRenderer:
            def __init__(self, *args, **kwargs):
                raise AssertionError(
                    "VisualRenderer must not be constructed when the toggle is off for all items"
                )

        ai_client = _FakeAIClient()
        # Toggle left disabled (default) for the only configured feed.
        sources_config = SourcesConfig(
            rss=[RSSSourceConfig(name="TestFeed", url="https://example.com/feed.xml")]
        )
        enricher = ContentEnricher(ai_client, sources_config=sources_config)
        items = [_rss_item(feed_name="TestFeed")]

        with patch("src.ai.visual_renderer.VisualRenderer", _ExplodingVisualRenderer):
            # Must not raise — proves VisualRenderer() is never called.
            asyncio.run(enricher.enrich_batch(items))

        assert "visual_extracted_content" not in items[0].metadata
        _assert_normal_enrichment_happened(items[0])

    def test_injected_renderer_bypasses_lazy_construction_entirely(self):
        class _ExplodingVisualRenderer:
            def __init__(self, *args, **kwargs):
                raise AssertionError("VisualRenderer must not be constructed when one was injected")

        ai_client = _FakeAIClient(
            vision_result=json.dumps({"differs_meaningfully": False, "extracted_content": ""})
        )
        renderer = _FakeRenderer(render_result=PNG_BYTES)
        sources_config = _sources_config_with_rss_enabled("TestFeed", enabled=True)
        enricher = ContentEnricher(ai_client, sources_config=sources_config, visual_renderer=renderer)
        items = [_rss_item(feed_name="TestFeed")]

        with patch("src.ai.visual_renderer.VisualRenderer", _ExplodingVisualRenderer):
            asyncio.run(enricher.enrich_batch(items))

        assert len(renderer.render_calls) == 1
        # Injected renderer stays set after the batch (not owned/torn down by enrich_batch).
        assert enricher._visual_renderer is renderer
