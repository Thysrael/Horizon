from __future__ import annotations

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.extractors import TrafilaturaExtractor
from src.extractors.trafilatura import ARTICLE_HEADERS
from src.models import TrafilaturaExtractorConfig

URL = "https://example.com/article"


def _extractor() -> TrafilaturaExtractor:
    return TrafilaturaExtractor(TrafilaturaExtractorConfig())


def _client(text: str = "<html><body><p>Article text.</p></body></html>", status: int = 200) -> AsyncMock:
    response = MagicMock()
    response.text = text
    response.raise_for_status.return_value = None
    if status >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=str(status), request=MagicMock(), response=MagicMock()
        )
    client = AsyncMock()
    client.get.return_value = response
    return client


def _trafilatura_mock(extracted: str) -> MagicMock:
    mod = MagicMock()
    mod.extract.return_value = extracted
    return mod


def test_returns_extracted_text():
    client = _client()
    with patch.dict(sys.modules, {"trafilatura": _trafilatura_mock("Extracted article text.")}):
        result = asyncio.run(_extractor().extract(URL, client))
    assert result == "Extracted article text."
    client.get.assert_awaited_once_with(
        URL,
        follow_redirects=False,
        headers=ARTICLE_HEADERS,
    )


def test_returns_none_when_trafilatura_returns_empty():
    client = _client()
    with patch.dict(sys.modules, {"trafilatura": _trafilatura_mock("")}):
        result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_on_http_error():
    client = _client(status=404)
    with patch.dict(sys.modules, {"trafilatura": _trafilatura_mock("text")}):
        result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_when_trafilatura_raises():
    client = _client()
    mock_traf = _trafilatura_mock("text")
    mock_traf.extract.side_effect = RuntimeError("parse error")
    with patch.dict(sys.modules, {"trafilatura": mock_traf}):
        result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_returns_none_when_not_installed():
    client = _client()
    with patch.dict(sys.modules, {"trafilatura": None}):
        result = asyncio.run(_extractor().extract(URL, client))
    assert result is None


def test_extraction_does_not_block_the_event_loop(monkeypatch):
    import threading
    import src.extractors.trafilatura as module
    import trafilatura

    heartbeat = threading.Event()

    def blocking_extract(*args, **kwargs):
        # A sibling task must be able to progress while the parser is busy.
        return "responsive" if heartbeat.wait(timeout=2.0) else "blocked"

    monkeypatch.setattr(trafilatura, "extract", blocking_extract)
    monkeypatch.setattr(module, "safe_request", AsyncMock(return_value=httpx.Response(
        200, text="<html>article</html>", request=httpx.Request("GET", "https://example.com/article"),
    )))

    async def run():
        async def tick():
            await asyncio.sleep(0)
            heartbeat.set()

        task = asyncio.create_task(tick())
        extractor = TrafilaturaExtractor(TrafilaturaExtractorConfig())
        result = await extractor.extract("https://example.com/article", AsyncMock())
        await task
        return result

    assert asyncio.run(run()) == "responsive"


def test_concurrent_extract_calls_across_instances_are_serialized(monkeypatch):
    import threading
    import time

    import trafilatura
    import src.extractors.trafilatura as module

    current = 0
    max_current = 0
    counter_lock = threading.Lock()

    def slow_extract(*args, **kwargs):
        nonlocal current, max_current
        with counter_lock:
            current += 1
            max_current = max(max_current, current)
        time.sleep(0.05)
        with counter_lock:
            current -= 1
        return "serialized"

    monkeypatch.setattr(trafilatura, "extract", slow_extract)
    monkeypatch.setattr(
        module,
        "safe_request",
        AsyncMock(
            return_value=httpx.Response(
                200,
                text="<html><body><p>Article text.</p></body></html>",
                request=httpx.Request("GET", URL),
            )
        ),
    )

    async def run():
        # Separate instances must still share the same process-wide lock.
        extractors = [_extractor() for _ in range(8)]
        client = AsyncMock()
        return await asyncio.gather(*[extractor.extract(URL, client) for extractor in extractors])

    assert asyncio.run(run()) == ["serialized"] * 8
    assert max_current == 1


def test_extract_releases_lock_after_exception(monkeypatch):
    import threading

    import trafilatura
    import src.extractors.trafilatura as module

    # Isolate a possible leaked-lock failure from subsequent tests.
    monkeypatch.setattr(module, "_EXTRACT_LOCK", threading.Lock())
    monkeypatch.setattr(
        module,
        "safe_request",
        AsyncMock(return_value=httpx.Response(
            200, text="<html>article</html>", request=httpx.Request("GET", URL),
        )),
    )
    extract = MagicMock(side_effect=[RuntimeError("parse error"), "recovered"])
    monkeypatch.setattr(trafilatura, "extract", extract)

    async def run():
        assert await _extractor().extract(URL, AsyncMock()) is None
        # Check the lock before starting another worker: a leaked lock should
        # fail promptly rather than leave asyncio.run waiting for a stuck thread.
        assert module._EXTRACT_LOCK.acquire(blocking=False)
        module._EXTRACT_LOCK.release()
        return await _extractor().extract(URL, AsyncMock())

    assert asyncio.run(run()) == "recovered"
    assert extract.call_count == 2


def test_concurrent_real_extract_returns_text(monkeypatch):
    import trafilatura
    import src.extractors.trafilatura as module

    paragraphs = "".join(
        f"<p>{'Useful background on the widget protocol. ' * 20}</p>"
        for _ in range(8)
    )
    html = (
        "<!DOCTYPE html><html><head><title>Widget notes</title></head>"
        f"<body><article><h1>Widget notes</h1>{paragraphs}</article></body></html>"
    )
    monkeypatch.setattr(
        module,
        "safe_request",
        AsyncMock(
            return_value=httpx.Response(
                200,
                text=html,
                request=httpx.Request("GET", URL),
            )
        ),
    )

    async def run():
        extractor = _extractor()
        client = AsyncMock()
        return await asyncio.gather(*[extractor.extract(URL, client) for _ in range(8)])

    results = asyncio.run(run())
    assert len(results) == 8
    assert all(isinstance(item, str) and "widget" in item.lower() for item in results)
    # Sanity: the real parser ran, not a skipped install path.
    assert trafilatura.extract(html)
