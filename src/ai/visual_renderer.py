"""Render-only visual extraction primitive: screenshot a URL with Playwright.

This module renders a URL to a raw PNG screenshot so that a vision-capable
AI client can inspect the real, rendered page content (as opposed to the
thin snippet/teaser text an RSS/GDELT/Google News feed already provides).

Design notes (see `.handoffs/00-ceo-brief.md`):
- This is a self-hosted render step only. It does not depend on the
  PixelRAG package, FAISS, or any embedding model — those were explicitly
  ruled out. A lightweight `pixelrag_render`-style PyPI package was not a
  realistic dependency (PixelRAG's render primitive isn't published as a
  standalone installable package), so the render step is implemented
  directly with Playwright's `page.screenshot()`, which is exactly the
  primitive PixelRAG itself uses under the hood.
- Mirrors the "optional dependency" pattern used by
  `src/scrapers/twitter_playwright.py`: Playwright is only imported inside
  a try/except so the rest of the codebase (including this module's own
  import) works fine even when Playwright/Chromium isn't installed. The
  `playwright` package is expected to live under a new `visual` extra in
  `pyproject.toml` (owned by a sibling task), not the existing `twitter`
  extra.
- `VisualRenderer` is a plain, config-agnostic, injectable primitive — it
  does not read Horizon's global `Config`/pydantic models. Callers (the
  enrichment/orchestrator wiring layer) are expected to construct it once
  with simple values (e.g. `timeout_ms` sourced from
  `visual_extraction.timeout_ms`) and inject it, matching `BaseScraper`'s
  constructor-injected `httpx.AsyncClient` pattern.
- Implemented as an async context manager that launches a single shared
  Chromium browser instance on `__aenter__` and closes it on `__aexit__`,
  reusing that browser across many `render()` calls (each call opens and
  closes its own page/context for isolation). This gives better
  performance than a launch-per-call design while still matching the
  "construct once, inject, reuse" DI spirit requested in the brief.
  Calling contract: `async with VisualRenderer(...) as renderer:` then
  `await renderer.render(url)` per item.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Optional Playwright import — gracefully degraded if not installed.
# Nothing else in this module requires Playwright to be importable.
try:
    from playwright.async_api import Browser, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None  # type: ignore[misc,assignment]


class VisualRenderer:
    """Renders a URL to a PNG screenshot using a shared headless Chromium browser.

    Usage:
        async with VisualRenderer(timeout_ms=15000) as renderer:
            png_bytes = await renderer.render("https://example.com/article")
            if png_bytes is not None:
                ...  # pass to a vision-capable AIClient

    `render()` never raises: it returns `None` on any failure (Playwright
    not installed, navigation timeout, network error, or any other
    exception), logging a warning instead. This is a hard requirement so
    that render failures degrade gracefully rather than dropping items or
    crashing the enrichment pipeline.
    """

    def __init__(
        self,
        timeout_ms: int = 15000,
        viewport_width: int = 1280,
        viewport_height: int = 1600,
        headless: bool = True,
    ):
        """Initialize renderer configuration (no browser is launched yet).

        Args:
            timeout_ms: Navigation timeout in milliseconds for `page.goto`.
            viewport_width: Viewport width in pixels for the rendered page.
            viewport_height: Viewport height in pixels for the rendered page.
            headless: Whether to launch Chromium headless (should stay True
                for server-side use).
        """
        self.timeout_ms = timeout_ms
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.headless = headless

        self._playwright_cm = None
        self._playwright = None
        self._browser: Optional["Browser"] = None

    async def __aenter__(self) -> "VisualRenderer":
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning(
                "Playwright not installed; VisualRenderer will no-op. "
                "Run: uv sync --extra visual && uv run playwright install chromium"
            )
            return self

        try:
            self._playwright_cm = async_playwright()
            self._playwright = await self._playwright_cm.__aenter__()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
        except Exception as exc:
            logger.warning("Failed to launch Playwright/Chromium: %s", exc)
            self._browser = None
            self._playwright = None
            self._playwright_cm = None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if self._browser is not None:
                await self._browser.close()
        except Exception as exc:
            logger.warning("Error closing Playwright browser: %s", exc)
        finally:
            self._browser = None

        if self._playwright_cm is not None:
            try:
                await self._playwright_cm.__aexit__(exc_type, exc_val, exc_tb)
            except Exception as exc:
                logger.warning("Error tearing down Playwright: %s", exc)
            finally:
                self._playwright_cm = None
                self._playwright = None

    async def render(self, url: str) -> Optional[bytes]:
        """Render `url` and return raw PNG screenshot bytes, or None on failure.

        Never raises. Returns None immediately if Playwright isn't
        installed, the shared browser failed to launch, or the browser
        wasn't started via `async with`. Any navigation/timeout/network
        error during rendering is caught, logged as a warning, and also
        results in None.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed; cannot render %s", url)
            return None

        if self._browser is None:
            logger.warning(
                "VisualRenderer browser is not started (use 'async with "
                "VisualRenderer() as renderer:'); cannot render %s",
                url,
            )
            return None

        context = None
        try:
            context = await self._browser.new_context(
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                }
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            # Brief extra wait so above-the-fold content (lazy images, JS
            # rendered text) has a chance to settle. Full network-idle is
            # unnecessary for a "does the real page differ from the RSS
            # snippet" check.
            await page.wait_for_timeout(min(2000, self.timeout_ms))
            screenshot_bytes = await page.screenshot(type="png")
            return screenshot_bytes
        except Exception as exc:
            logger.warning("Failed to render %s: %s", url, exc)
            return None
        finally:
            if context is not None:
                try:
                    await context.close()
                except Exception as exc:
                    logger.debug("Error closing render context for %s: %s", url, exc)
