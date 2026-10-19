"""Firecrawl-based article extractor."""

import logging
import os
from typing import Optional

import httpx

from .base import BaseExtractor
from ..models import FirecrawlExtractorConfig

logger = logging.getLogger(__name__)

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"


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
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Firecrawl scrape failed for %s: %s", url, e)
            return None

        try:
            return response.json()["data"]["markdown"] or None
        except (ValueError, KeyError, TypeError) as e:
            logger.warning("Unexpected Firecrawl response for %s: %s", url, e)
            return None
