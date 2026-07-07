"""Content enrichment using AI (second-pass analysis).

For items that pass the score threshold, this module:
1. Searches the web for relevant context (via DuckDuckGo)
2. Feeds search results + item content to AI to generate grounded background knowledge
"""

import asyncio
import json
import re
import sys
import os
from typing import Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, MofNCompleteColumn
from ddgs import DDGS

from .client import AIClient
from .prompts import (
    CONCEPT_EXTRACTION_SYSTEM, CONCEPT_EXTRACTION_USER,
    CONTENT_ENRICHMENT_SYSTEM, CONTENT_ENRICHMENT_USER,
    VISUAL_EXTRACTION_SYSTEM, VISUAL_EXTRACTION_USER,
)
from .utils import parse_json_response
from ..models import ContentItem, SourceType, SourcesConfig, VisualExtractionConfig

# Source types eligible for the render-only visual extraction sub-step. Any
# other source type (GitHub, HackerNews, Reddit, Telegram, Twitter, OpenBB,
# OSSInsight) never even reaches the gating check.
_VISUAL_EXTRACTION_SOURCE_TYPES = {
    SourceType.RSS,
    SourceType.GDELT,
    SourceType.GOOGLE_NEWS,
}


class ContentEnricher:
    """Enriches high-scoring content items with background knowledge."""

    def __init__(
        self,
        ai_client: AIClient,
        sources_config: Optional[SourcesConfig] = None,
        visual_renderer: Optional[Any] = None,
    ):
        """Initialize the enricher.

        Args:
            ai_client: AI client used for concept extraction, enrichment,
                translation, and (if the provider supports it) vision calls.
            sources_config: Optional `SourcesConfig` used only to resolve the
                per-item visual-extraction toggle (RSS per-feed, or GDELT /
                Google News source-level). `None` (the default) disables the
                visual-extraction sub-step entirely for this instance, which
                keeps `ContentEnricher(ai_client)` a fully backward-compatible
                call pattern.
            visual_renderer: Optional pre-constructed renderer object exposing
                an async `render(url: str) -> Optional[bytes]` method (e.g. a
                `VisualRenderer` already entered via `async with`, or a mock
                for tests). If not provided, `enrich_batch` lazily constructs
                and manages a real `VisualRenderer` for the duration of the
                batch, but only if at least one item in that batch actually
                needs it.
        """
        self.client = ai_client
        self.sources_config = sources_config
        self._visual_renderer = visual_renderer

    def _get_concurrency(self) -> int:
        """Return the configured enrichment concurrency, clamped to 1 or above."""
        config = getattr(self.client, "config", None)
        concurrency = getattr(config, "enrichment_concurrency", 1)
        return max(concurrency, 1)

    def _resolve_visual_extraction(
        self, item: ContentItem
    ) -> Optional[VisualExtractionConfig]:
        """Resolve the per-item visual-extraction config, or None if disabled.

        Returns None (treat as disabled, no-op) whenever:
        - `sources_config` was never provided to this instance.
        - `item.source_type` is not RSS/GDELT/GOOGLE_NEWS.
        - The resolved config's `.enabled` is False.
        - No matching RSS feed config is found by `feed_name`.
        - The GDELT/Google News source config is not set (`None`).
        """
        if self.sources_config is None:
            return None
        if item.source_type not in _VISUAL_EXTRACTION_SOURCE_TYPES:
            return None

        ve_config: Optional[VisualExtractionConfig] = None
        if item.source_type == SourceType.RSS:
            feed_name = item.metadata.get("feed_name")
            for rss_source in self.sources_config.rss:
                if rss_source.name == feed_name:
                    ve_config = rss_source.visual_extraction
                    break
        elif item.source_type == SourceType.GDELT:
            if self.sources_config.gdelt is not None:
                ve_config = self.sources_config.gdelt.visual_extraction
        elif item.source_type == SourceType.GOOGLE_NEWS:
            if self.sources_config.google_news is not None:
                ve_config = self.sources_config.google_news.visual_extraction

        if ve_config is None or not ve_config.enabled:
            return None
        return ve_config

    def _batch_needs_visual_extraction(self, items: List[ContentItem]) -> bool:
        """True if at least one item in the batch resolves to an enabled toggle."""
        return any(self._resolve_visual_extraction(item) is not None for item in items)

    async def enrich_batch(self, items: List[ContentItem]) -> None:
        """Enrich items in-place with background knowledge.

        Args:
            items: Content items to enrich (modified in-place)
        """
        concurrency = self._get_concurrency()
        semaphore = asyncio.Semaphore(concurrency)

        # Lazily construct and enter a real VisualRenderer for this batch only
        # if: (a) no renderer was already injected via the constructor, and
        # (b) at least one item in this batch actually needs one. This keeps
        # the toggle-off path free of any Playwright import/launch attempt.
        owns_renderer = False
        renderer_cm = None
        if self._visual_renderer is None and self._batch_needs_visual_extraction(items):
            from .visual_renderer import VisualRenderer

            timeout_candidates = [
                cfg.timeout_ms
                for item in items
                if (cfg := self._resolve_visual_extraction(item)) is not None
            ]
            timeout_ms = max(timeout_candidates) if timeout_candidates else 15000
            renderer_cm = VisualRenderer(timeout_ms=timeout_ms)
            self._visual_renderer = await renderer_cm.__aenter__()
            owns_renderer = True

        try:
            async def _process(item: ContentItem, progress_task) -> None:
                async with semaphore:
                    try:
                        await self._enrich_item(item)
                    except Exception as e:
                        print(f"Error enriching item {item.id}: {e}, falling back to translation")
                        await self._translate_item(item)
                progress.advance(progress_task)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                transient=True,
            ) as progress:
                task = progress.add_task("Enriching", total=len(items))
                coros = [
                    _process(item, task) for item in items
                ]
                await asyncio.gather(*coros)
        finally:
            if owns_renderer and renderer_cm is not None:
                await renderer_cm.__aexit__(None, None, None)
                self._visual_renderer = None

    async def _web_search(self, query: str, max_results: int = 3) -> list:
        """Search the web for context via DuckDuckGo.

        Returns:
            List of dicts with keys: title, url, body
        """
        try:
            # Suppress primp "Impersonate ... does not exist" stderr warning
            stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")
            try:
                ddgs = DDGS()
                results = await asyncio.to_thread(ddgs.text, query, max_results=max_results)
            finally:
                sys.stderr.close()
                sys.stderr = stderr
        except Exception:
            return []

        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "body": r.get("body", "")}
            for r in (results or [])
        ]

    @staticmethod
    def _parse_json_response(response: str) -> Optional[dict]:
        """Try multiple strategies to extract a JSON object from an AI response.

        Returns the parsed dict, or None if all strategies fail.
        """
        return parse_json_response(response)

    async def _extract_concepts(self, item: ContentItem, content_text: str) -> List[str]:
        """Ask AI to identify concepts that need explanation.

        Args:
            item: Content item
            content_text: Extracted content text

        Returns:
            List of search queries for concepts that need explanation
        """
        user_prompt = CONCEPT_EXTRACTION_USER.format(
            title=item.title,
            summary=item.ai_summary or item.title,
            tags=", ".join(item.ai_tags) if item.ai_tags else "",
            content=content_text[:1000],
        )

        try:
            response = await self.client.complete(
                system=CONCEPT_EXTRACTION_SYSTEM,
                user=user_prompt,
            )
            result = self._parse_json_response(response)
            if result is None:
                return []
            queries = result.get("queries", [])
            return queries[:3]
        except Exception:
            return []

    async def _maybe_visual_extract(self, item: ContentItem, content_text: str) -> str:
        """Render-and-vision sub-step: try to replace the thin snippet with the
        real rendered article content, for RSS/GDELT/Google News items whose
        per-source visual-extraction toggle is enabled.

        This never raises: any failure (gate doesn't match, no renderer
        available, render failure/timeout, non-vision-capable AI client,
        malformed JSON response, etc.) is swallowed and the original
        `content_text` is returned unchanged, exactly as if the toggle were
        off.

        Args:
            item: Content item (may be updated in-place via metadata)
            content_text: The existing (thin) content text already extracted
                from the item's feed/API snippet

        Returns:
            str: Either the original `content_text`, or AI-extracted real
            article content if the vision step succeeded and indicated the
            real page differs meaningfully from the snippet.
        """
        ve_config = self._resolve_visual_extraction(item)
        if ve_config is None:
            return content_text

        renderer = self._visual_renderer
        if renderer is None:
            return content_text

        try:
            png_bytes = await renderer.render(str(item.url))
            if png_bytes is None:
                return content_text

            user_prompt = VISUAL_EXTRACTION_USER.format(
                title=item.title,
                snippet=content_text[:4000] if content_text else "(no snippet content available)",
            )
            response = await self.client.complete_vision(
                system=VISUAL_EXTRACTION_SYSTEM,
                user=user_prompt,
                image_data=png_bytes,
            )
            result = self._parse_json_response(response)
            if not result:
                return content_text

            if result.get("differs_meaningfully") and result.get("extracted_content"):
                extracted = str(result["extracted_content"]).strip()[:4000]
                if extracted:
                    item.metadata["visual_extracted_content"] = extracted
                    return extracted
            return content_text
        except Exception as e:
            print(f"Visual extraction failed for item {item.id}: {e}")
            return content_text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=10)
    )
    async def _enrich_item(self, item: ContentItem) -> None:
        """Enrich a single item with background knowledge.

        Steps:
        0. (RSS/GDELT/Google News, if enabled) Render the article URL and ask
           a vision-capable AI whether the real page differs meaningfully
           from the thin snippet, using the extracted real content in place
           of the snippet if so
        1. Ask AI which concepts in the news need explanation
        2. Search the web for those concepts
        3. Ask AI to generate background based on search results

        Args:
            item: Content item to enrich (modified in-place via metadata)
        """
        # Extract content text and comments separately
        content_text = ""
        comments_text = ""
        if item.content:
            if "--- Top Comments ---" in item.content:
                main, comments_part = item.content.split("--- Top Comments ---", 1)
                content_text = main.strip()[:4000]
                comments_text = comments_part.strip()[:2000]
            else:
                content_text = item.content[:4000]

        # Step 0: render-only visual extraction sub-step (RSS/GDELT/Google
        # News only, opt-in, gracefully degrades on any failure). May
        # replace content_text with AI-extracted real article content,
        # which then grounds the rest of this method (concept extraction,
        # web search, and the final enrichment call).
        content_text = await self._maybe_visual_extract(item, content_text)

        # Step 1: AI identifies concepts to explain
        queries = await self._extract_concepts(item, content_text)

        # Step 2: Search web for each concept
        all_results = []
        web_sections = []
        for query in queries:
            results = await self._web_search(query)
            all_results.extend(results)
            if results:
                lines = [f"- [{r['title']}]({r['url']}): {r['body']}" for r in results]
                web_sections.append(f"**{query}:**\n" + "\n".join(lines))
        web_context = "\n\n".join(web_sections) if web_sections else ""

        # Index of available URLs for citation validation
        available_urls = {r["url"]: r["title"] for r in all_results if r.get("url")}

        # Step 3: AI generates background grounded in search results
        user_prompt = CONTENT_ENRICHMENT_USER.format(
            title=item.title,
            url=str(item.url),
            summary=item.ai_summary or item.title,
            score=item.ai_score or 0,
            reason=item.ai_reason or "",
            tags=", ".join(item.ai_tags) if item.ai_tags else "",
            content=content_text,
            comments_section=f"\n**Community Comments:**\n{comments_text}" if comments_text else "",
            web_context=web_context or "No web search results available.",
        )

        response = await self.client.complete(
            system=CONTENT_ENRICHMENT_SYSTEM,
            user=user_prompt,
        )

        # Parse JSON response with robust fallback
        result = self._parse_json_response(response)
        if result is None:
            # Gracefully degrade: fall back to a lightweight translation
            # instead of dropping the item untranslated.
            print(f"Warning: could not parse enrichment response for {item.id}, falling back to translation")
            await self._translate_item(item)
            return

        # Combine structured sub-fields into per-language detailed_summary
        for lang in ("en", "zh"):
            if result.get(f"title_{lang}"):
                val = result[f"title_{lang}"]
                item.metadata[f"title_{lang}"] = val.get("text") or str(val) if isinstance(val, dict) else str(val)

            parts = []
            for field in ("whats_new", "why_it_matters", "key_details"):
                text = result.get(f"{field}_{lang}", "").strip()
                if text:
                    parts.append(text)
            if parts:
                item.metadata[f"detailed_summary_{lang}"] = " ".join(parts)

            if result.get(f"background_{lang}"):
                val = result[f"background_{lang}"]
                item.metadata[f"background_{lang}"] = val.get("text") or str(val) if isinstance(val, dict) else str(val)

            if result.get(f"community_discussion_{lang}"):
                val = result[f"community_discussion_{lang}"]
                item.metadata[f"community_discussion_{lang}"] = val.get("text") or str(val) if isinstance(val, dict) else str(val)

        # Store citation sources — only URLs that actually came from our search results
        if result.get("sources") and available_urls:
            valid = [
                {"url": u, "title": available_urls[u]}
                for u in result["sources"]
                if u in available_urls
            ]
            if valid:
                item.metadata["sources"] = valid

        # Backward-compatible fallback fields (English as default)
        item.metadata["detailed_summary"] = item.metadata.get("detailed_summary_en", "")
        item.metadata["background"] = item.metadata.get("background_en", "")
        item.metadata["community_discussion"] = item.metadata.get("community_discussion_en", "")

    async def _translate_item(self, item: ContentItem) -> None:
        """Lightweight translation fallback: when full enrichment fails, at least
        translate the title and summary to Chinese so the item is not dropped."""
        try:
            response = await self.client.complete(
                system="You are a translator. Translate to Simplified Chinese. Return only valid JSON, no other text.",
                user=(
                    f'Title: {item.title}\n'
                    f'Summary: {item.ai_summary or item.title}\n\n'
                    'Return JSON:\n'
                    '{"title_zh": "<中文标题>", "summary_zh": "<用中文写1-2句摘要>"}'
                ),
            )
            result = self._parse_json_response(response)
            if result:
                if result.get("title_zh"):
                    item.metadata["title_zh"] = result["title_zh"]
                if result.get("summary_zh"):
                    item.metadata["detailed_summary_zh"] = result["summary_zh"]
        except Exception:
            pass
