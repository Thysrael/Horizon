from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.extractors import FirecrawlExtractor
from src.extractors.firecrawl import FIRECRAWL_SCRAPE_URL
from src.models import FirecrawlExtractorConfig

URL = "https://example.com/article"


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")


def _extractor(**kwargs) -> FirecrawlExtractor:
    return FirecrawlExtractor(FirecrawlExtractorConfig(**kwargs))


def _client(payload=None, status: int = 200) -> AsyncMock:
    response = MagicMock()
    response.json.return_value = payload if payload is not None else {
        "success": True,
        "data": {"markdown": "# Title\n\nArticle text."},
    }
    response.raise_for_status.return_value = None
    if status >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=str(status), request=MagicMock(), response=MagicMock()
        )
    client = AsyncMock()
    client.post.return_value = response
    return client


def test_returns_markdown():
    client = _client()
    result = asyncio.run(_extractor().extract(URL, client))
    assert result == "# Title\n\nArticle text."
    client.post.assert_awaited_once_with(
        FIRECRAWL_SCRAPE_URL,
        headers={"Authorization": "Bearer fc-test"},
        json={
            "url": URL,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "integration": "_horizon",
        },
    )


def test_uses_configured_env_var_and_options(monkeypatch):
    monkeypatch.setenv("MY_FIRECRAWL_KEY", "fc-other")
    client = _client()
    asyncio.run(_extractor(api_key_env="MY_FIRECRAWL_KEY", only_main_content=False).extract(URL, client))
    _, kwargs = client.post.call_args
    assert kwargs["headers"] == {"Authorization": "Bearer fc-other"}
    assert kwargs["json"]["onlyMainContent"] is False


def test_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("FIRECRAWL_API_KEY")
    client = _client()
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None
    client.post.assert_not_awaited()


def test_returns_none_on_http_error():
    client = _client(status=401)
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_on_timeout():
    client = AsyncMock()
    client.post.side_effect = httpx.ReadTimeout("timed out")
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_on_empty_markdown():
    client = _client({"success": True, "data": {"markdown": ""}})
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_on_unexpected_response():
    client = _client({"success": False, "error": "boom"})
    result = asyncio.run(_extractor().extract(URL, client))
    assert result is None
