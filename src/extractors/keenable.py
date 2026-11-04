"""Keenable-based article extractor."""

import logging
import os
from typing import Optional

import httpx

from .base import BaseExtractor
from ..models import KeenableExtractorConfig

logger = logging.getLogger(__name__)

KEENABLE_FETCH_URL = "https://api.keenable.ai/v1/fetch"
# Keyless twin of the fetch endpoint; an API key only raises the rate limits.
KEENABLE_PUBLIC_FETCH_URL = "https://api.keenable.ai/v1/fetch/public"


class KeenableExtractor(BaseExtractor):
    def __init__(self, config: KeenableExtractorConfig):
        self._config = config

    async def extract(self, url: str, client: httpx.AsyncClient) -> Optional[str]:
        api_key = (os.environ.get(self._config.api_key_env) or "").strip()
        endpoint = KEENABLE_FETCH_URL if api_key else KEENABLE_PUBLIC_FETCH_URL
        headers = {"X-Keenable-Title": "Horizon"}
        if api_key:
            headers["X-API-Key"] = api_key

        try:
            response = await client.get(endpoint, params={"url": url}, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Keenable fetch failed for %s: %s", url, e)
            return None

        try:
            payload = response.json()
            if not isinstance(payload, dict):
                logger.warning("Unexpected Keenable response for %s", url)
                return None
            content = payload.get("content")
            return content if isinstance(content, str) and content.strip() else None
        except ValueError as e:
            logger.warning("Unexpected Keenable response for %s: %s", url, e)
            return None
