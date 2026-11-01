"""Outcrawl-based article extractor."""

import logging
import os
from typing import Optional

import httpx

from .base import BaseExtractor
from ..models import OutcrawlExtractorConfig

logger = logging.getLogger(__name__)

OUTCRAWL_SCRAPE_URL = "https://api.outcrawl.ai/v1/scrape"
# Rendering a page can take longer than a plain fetch, so the scrape gets its own budget.
_SCRAPE_TIMEOUT_S = 65.0


class OutcrawlExtractor(BaseExtractor):
    def __init__(self, config: OutcrawlExtractorConfig):
        self._config = config

    async def extract(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        api_key = os.environ.get(self._config.api_key_env)
        if not api_key:
            logger.warning(
                "Outcrawl API key not found in env var '%s'; skipping extraction for %s",
                self._config.api_key_env,
                url,
            )
            return None

        try:
            response = await client.post(
                OUTCRAWL_SCRAPE_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": self._config.only_main_content,
                },
                timeout=_SCRAPE_TIMEOUT_S,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Outcrawl scrape failed for %s: %s", url, e)
            return None

        try:
            payload = response.json()
            if not isinstance(payload, dict):
                logger.warning("Unexpected Outcrawl response for %s", url)
                return None
            markdown = payload.get("markdown")
            return markdown if isinstance(markdown, str) and markdown.strip() else None
        except ValueError as e:
            logger.warning("Unexpected Outcrawl response for %s: %s", url, e)
            return None
