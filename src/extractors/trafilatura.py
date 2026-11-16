"""Trafilatura-based article extractor."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from .base import BaseExtractor
from ..models import TrafilaturaExtractorConfig
from ..url_security import UnsafeURLError, safe_request

logger = logging.getLogger(__name__)

ARTICLE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass(frozen=True)
class ExtractedArticle:
    """Article text extracted from one URL, plus an optional title and error."""

    content: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


class TrafilaturaExtractor(BaseExtractor):
    def __init__(self, config: TrafilaturaExtractorConfig):
        self._config = config

    async def extract(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        return (await self._extract(url, client, include_title=False)).content

    async def extract_article(self, url: str, client: httpx.AsyncClient) -> ExtractedArticle:
        """Fetch a page and extract its main text with the RSS article settings."""

        return await self._extract(url, client, include_title=True)

    async def _extract(
        self,
        url: str,
        client: httpx.AsyncClient,
        *,
        include_title: bool,
    ) -> ExtractedArticle:
        try:
            import trafilatura
        except ImportError:
            logger.warning("trafilatura is not installed; install with: uv pip install trafilatura>=2.1.0")
            return ExtractedArticle(error="trafilatura is not installed")

        try:
            response = await safe_request(client, "GET", url, headers=ARTICLE_HEADERS)
            response.raise_for_status()
        except (httpx.HTTPError, UnsafeURLError) as e:
            logger.warning("Failed to fetch article %s: %s", url, e)
            return ExtractedArticle(error=f"{type(e).__name__}: {e}")

        try:
            content = await asyncio.to_thread(
                trafilatura.extract,
                response.text,
                favor_precision=self._config.favor_precision,
                favor_recall=self._config.favor_recall,
            ) or None
        except Exception as e:
            logger.warning("trafilatura extraction failed for %s: %s", url, e)
            return ExtractedArticle(error=f"{type(e).__name__}: {e}")

        title = _title_from_html(trafilatura, response.text) if include_title else None
        if not content:
            return ExtractedArticle(
                title=title,
                error="no article content extracted" if include_title else None,
            )
        return ExtractedArticle(content=content, title=title)


def _title_from_html(trafilatura_module, html: str) -> Optional[str]:
    """Read a title from trafilatura metadata when the page provides one."""

    extract_metadata = getattr(trafilatura_module, "extract_metadata", None)
    if extract_metadata is None:
        return None
    try:
        metadata = extract_metadata(html)
    except Exception:
        logger.debug("trafilatura metadata extraction failed", exc_info=True)
        return None
    title = getattr(metadata, "title", None)
    if not isinstance(title, str):
        return None
    stripped = title.strip()
    return stripped or None
