"""SpecStream-based article extractor."""

import logging
import os
from typing import Optional

import httpx

from .base import BaseExtractor
from ..models import SpecStreamExtractorConfig

logger = logging.getLogger(__name__)

SPECSTREAM_EXTRACT_URL = "https://api.specstream.ai/v1/extract"
# The Extract API gives each URL up to 30 seconds; allow time for the response.
_EXTRACT_TIMEOUT_S = 35.0


class SpecStreamExtractor(BaseExtractor):
    def __init__(self, config: SpecStreamExtractorConfig):
        self._config = config

    async def extract(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        api_key = os.environ.get(self._config.api_key_env)
        if not api_key:
            logger.warning(
                "SpecStream API key not found in env var '%s'; skipping extraction for %s",
                self._config.api_key_env,
                url,
            )
            return None

        try:
            response = await client.post(
                SPECSTREAM_EXTRACT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"urls": [url], "format": "markdown"},
                timeout=_EXTRACT_TIMEOUT_S,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("SpecStream extract failed for %s: %s", url, e)
            return None

        try:
            page = response.json()["data"]["results"][0]
            if page.get("status") != "ok":
                logger.warning("SpecStream could not read %s: %s", url, page.get("status"))
                return None
            text = page.get("text")
            return text if isinstance(text, str) and text.strip() else None
        except (ValueError, KeyError, IndexError, TypeError, AttributeError) as e:
            logger.warning("Unexpected SpecStream response for %s: %s", url, e)
            return None
