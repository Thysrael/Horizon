"""Tests for VisualRenderer (src/ai/visual_renderer.py).

Playwright is NOT installed in this environment (confirmed), so every test
here fakes the Playwright surface via unittest.mock — no real browser is
ever launched and no network call is ever made. Success-path tests patch
`PLAYWRIGHT_AVAILABLE` to True and inject a fake `async_playwright` hook
directly onto the module (the module only binds that name when the real
import succeeds, so we add it back with monkeypatch's `raising=False`).
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import src.ai.visual_renderer as visual_renderer_module
from src.ai.visual_renderer import VisualRenderer


def _make_fake_playwright(mock_browser, launch_side_effect=None):
    """Build a fake `async_playwright()` callable plus its launch chain."""
    fake_playwright_cm = AsyncMock()
    fake_playwright_instance = MagicMock()
    if launch_side_effect is not None:
        fake_playwright_instance.chromium.launch = AsyncMock(side_effect=launch_side_effect)
    else:
        fake_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
    fake_playwright_cm.__aenter__ = AsyncMock(return_value=fake_playwright_instance)
    fake_playwright_cm.__aexit__ = AsyncMock(return_value=None)

    def _async_playwright():
        return fake_playwright_cm

    return _async_playwright, fake_playwright_cm, fake_playwright_instance


class TestPlaywrightUnavailable:
    """PLAYWRIGHT_AVAILABLE = False (Playwright not installed) is a no-op, never raises."""

    def test_render_returns_none_when_playwright_not_installed(self, monkeypatch):
        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", False)
        renderer = VisualRenderer()

        result = asyncio.run(renderer.render("https://example.com/article"))

        assert result is None

    def test_aenter_is_noop_when_playwright_not_installed(self, monkeypatch, caplog):
        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", False)
        renderer = VisualRenderer()

        with caplog.at_level(logging.WARNING):
            entered = asyncio.run(renderer.__aenter__())

        assert entered is renderer
        assert renderer._browser is None
        assert any("Playwright not installed" in r.message for r in caplog.records)

    def test_full_context_manager_usage_never_raises_when_unavailable(self, monkeypatch):
        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", False)

        async def scenario():
            async with VisualRenderer() as renderer:
                return await renderer.render("https://example.com")

        result = asyncio.run(scenario())
        assert result is None


class TestContextManagerLifecycle:
    """__aenter__/__aexit__ launch and close a single shared browser instance."""

    def test_aenter_launches_browser_and_aexit_closes_it(self, monkeypatch):
        mock_browser = AsyncMock()
        fake_async_playwright, fake_cm, fake_instance = _make_fake_playwright(mock_browser)

        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)
        monkeypatch.setattr(
            visual_renderer_module, "async_playwright", fake_async_playwright, raising=False
        )

        captured = {}

        async def scenario():
            async with VisualRenderer(headless=True) as renderer:
                captured["browser_during"] = renderer._browser
            captured["browser_after"] = renderer._browser

        asyncio.run(scenario())

        fake_instance.chromium.launch.assert_awaited_once_with(headless=True)
        assert captured["browser_during"] is mock_browser
        mock_browser.close.assert_awaited_once()
        fake_cm.__aexit__.assert_awaited_once()
        # Browser reference is cleared after teardown.
        assert captured["browser_after"] is None

    def test_aenter_handles_launch_failure_gracefully(self, monkeypatch, caplog):
        fake_async_playwright, fake_cm, fake_instance = _make_fake_playwright(
            None, launch_side_effect=RuntimeError("chromium failed to launch")
        )

        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)
        monkeypatch.setattr(
            visual_renderer_module, "async_playwright", fake_async_playwright, raising=False
        )

        async def scenario():
            async with VisualRenderer() as renderer:
                return renderer

        with caplog.at_level(logging.WARNING):
            renderer = asyncio.run(scenario())

        assert renderer._browser is None
        assert any("Failed to launch Playwright" in r.message for r in caplog.records)

    def test_aexit_handles_close_failure_without_raising(self, monkeypatch):
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock(side_effect=RuntimeError("close failed"))
        fake_async_playwright, fake_cm, fake_instance = _make_fake_playwright(mock_browser)

        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)
        monkeypatch.setattr(
            visual_renderer_module, "async_playwright", fake_async_playwright, raising=False
        )

        async def scenario():
            async with VisualRenderer() as renderer:
                pass

        # Must not raise even though browser.close() blew up.
        asyncio.run(scenario())
        mock_browser.close.assert_awaited_once()


class TestRenderSuccess:
    """render() returns screenshot bytes from a mocked page.screenshot()."""

    def test_render_returns_screenshot_bytes(self, monkeypatch):
        png_bytes = b"\x89PNG-fake-bytes"

        mock_page = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=png_bytes)
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)

        renderer = VisualRenderer(timeout_ms=5000)
        renderer._browser = mock_browser  # simulate an already-entered renderer

        result = asyncio.run(renderer.render("https://example.com/article"))

        assert result == png_bytes
        mock_page.goto.assert_awaited_once()
        goto_args, goto_kwargs = mock_page.goto.call_args
        assert goto_args[0] == "https://example.com/article"
        assert goto_kwargs["timeout"] == 5000
        mock_page.screenshot.assert_awaited_once_with(type="png")
        mock_context.close.assert_awaited_once()

    def test_render_returns_none_when_browser_not_started(self, monkeypatch):
        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)
        renderer = VisualRenderer()  # never entered via `async with`

        result = asyncio.run(renderer.render("https://example.com"))

        assert result is None


class TestRenderFailureModes:
    """Any failure during render() degrades to None + a warning log, never raises."""

    def test_render_returns_none_and_logs_warning_on_navigation_timeout(self, monkeypatch, caplog):
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=TimeoutError("Navigation timeout of 15000ms exceeded"))
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)
        renderer = VisualRenderer()
        renderer._browser = mock_browser

        with caplog.at_level(logging.WARNING):
            result = asyncio.run(renderer.render("https://example.com/slow-page"))

        assert result is None
        assert any("Failed to render" in r.message for r in caplog.records)
        # Context must still be cleaned up even on failure.
        mock_context.close.assert_awaited_once()

    def test_render_returns_none_on_new_context_failure(self, monkeypatch):
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(side_effect=RuntimeError("network down"))

        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)
        renderer = VisualRenderer()
        renderer._browser = mock_browser

        result = asyncio.run(renderer.render("https://example.com"))

        assert result is None

    def test_render_never_raises_out_of_the_coroutine(self, monkeypatch):
        """Belt-and-suspenders: render() must not propagate ANY exception type."""
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(side_effect=Exception("anything at all"))
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        monkeypatch.setattr(visual_renderer_module, "PLAYWRIGHT_AVAILABLE", True)
        renderer = VisualRenderer()
        renderer._browser = mock_browser

        try:
            result = asyncio.run(renderer.render("https://example.com"))
        except Exception as exc:  # pragma: no cover - this is exactly what we assert against
            raise AssertionError(f"render() must never raise, but raised: {exc}")

        assert result is None
