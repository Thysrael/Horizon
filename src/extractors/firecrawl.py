"""Firecrawl-based article extractor."""

import logging
import os
from typing import Optional

import httpx

from .base import BaseExtractor
from ..models import FirecrawlExtractorConfig

logger = logging.getLogger(__name__)

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"
_SCRAPE_TIMEOUT_MS = 60_000


class FirecrawlExtractor(BaseExtractor):
    def __init__(self, config: FirecrawlExtractorConfig):
        self._config = config

    async def extract(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        api_key = os.environ.get(self._config.api_key_env)
        if not api_key:
            logger.warning(
                "Firecrawl API key not found in env var '%s'; skipping extraction for %s",
                self._config.api_key_env,
                url,
            )
            return None

        try:
            response = await client.post(
                FIRECRAWL_SCRAPE_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": self._config.only_main_content,
                    "integration": "_horizon",
                    "timeout": _SCRAPE_TIMEOUT_MS,
                },
                # Allow the server's scrape budget plus time for the response.
                timeout=_SCRAPE_TIMEOUT_MS / 1000 + 5,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Firecrawl scrape failed for %s: %s", url, e)
            return None

        try:
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("success") is not True:
                logger.warning("Firecrawl scrape did not report success for %s", url)
                return None
            markdown = payload["data"]["markdown"]
            return markdown if isinstance(markdown, str) and markdown.strip() else None
        except (ValueError, KeyError, TypeError) as e:
            logger.warning("Unexpected Firecrawl response for %s: %s", url, e)
            return None
