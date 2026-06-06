"""Twitter scraper using Playwright + Cookie (replaces Apify)."""

import asyncio
import glob
import hashlib
import json
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..models import ContentItem, SourceType, TwitterConfig
from .base import BaseScraper

logger = logging.getLogger(__name__)

# Optional Playwright imports — gracefully degraded if not installed
try:
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Stealth = None  # type: ignore[misc,assignment]


def _get_proxy() -> str:
    """Resolve proxy from common env vars (PROXY, http_proxy, all_proxy)."""
    for key in ("PROXY", "https_proxy", "http_proxy", "all_proxy"):
        val = os.getenv(key, "").strip()
        if val:
            return val
    return ""


PROXY = _get_proxy()


def _load_browser_cookies(file_path: str) -> list[dict]:
    """Read browser-exported cookie JSON and convert to Playwright format."""
    if not Path(file_path).exists():
        return []
    with open(file_path, encoding="utf-8") as f:
        cookies = json.load(f)
    pw_cookies = []
    for c in cookies:
        pc: dict = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
            "httpOnly": c.get("httpOnly", False),
        }
        if c.get("expirationDate"):
            pc["expires"] = c["expirationDate"]
        pw_cookies.append(pc)
    return pw_cookies


class TwitterPlaywrightScraper(BaseScraper):
    """Fetch tweets via Playwright + Cookie using GraphQL interception (free alternative to Apify)."""

    def __init__(self, config: TwitterConfig, http_client=None):
        super().__init__(config.model_dump(), http_client)
        self.twitter_config = config

    async def fetch(self, since: datetime) -> List[ContentItem]:
        if not self.twitter_config.enabled:
            return []

        users = [u.strip().lstrip("@") for u in self.twitter_config.users if u.strip()]
        if not users:
            logger.debug("No Twitter users configured, skipping.")
            return []

        if not PLAYWRIGHT_AVAILABLE:
            logger.warning(
                "Playwright not installed. Run: uv sync --extra twitter && uv run playwright install chromium"
            )
            return []

        cookie_dir = Path(self.twitter_config.cookie_dir)
        pattern = self.twitter_config.cookie_file_pattern
        cookie_files = sorted(cookie_dir.glob(pattern))
        if not cookie_files:
            logger.warning("No cookie files found matching %s in %s", pattern, cookie_dir)
            return []

        logger.info(
            "Fetching Twitter (Playwright) for %d users using %d cookie sets",
            len(users),
            len(cookie_files),
        )

        all_items: List[ContentItem] = []
        failed_users: list[tuple[str, int]] = []
        lock = asyncio.Lock()

        async with Stealth().use_async(async_playwright()) as p:  # type: ignore[union-attr]
            launch_kwargs: dict = {"headless": True}
            if PROXY:
                launch_kwargs["proxy"] = {"server": PROXY}
            browser = await p.chromium.launch(**launch_kwargs)

            contexts = []
            for i, cf in enumerate(cookie_files):
                cookies = _load_browser_cookies(str(cf))
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/13{i}.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                    timezone_id="UTC",
                    color_scheme="dark",
                )
                if cookies:
                    await ctx.add_cookies(cookies)
                contexts.append(ctx)

            # Warm-up each context by visiting x.com/home
            for i, ctx in enumerate(contexts):
                page = await ctx.new_page()
                try:
                    await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)
                    logger.info("Cookie #%d warm-up done", i + 1)
                except Exception as exc:
                    logger.warning("Cookie #%d warm-up failed: %s", i + 1, exc)
                finally:
                    await page.close()

            num_contexts = len(contexts)

            async def process_queue(context_idx: int, queue: list[str], is_retry: bool = False):
                ctx = contexts[context_idx]
                consecutive_failures = 0

                for username in queue:
                    wait_time = (
                        random.uniform(5.0, 10.0) if not is_retry else random.uniform(10.0, 20.0)
                    )
                    await asyncio.sleep(wait_time)

                    if consecutive_failures >= 5:
                        logger.warning("Context #%d cooling down (30s)", context_idx + 1)
                        await asyncio.sleep(30)
                        consecutive_failures = 0

                    logger.info("Scraping @%s with cookie #%d...", username, context_idx + 1)
                    tweets = await self._scrape_user(ctx, username, since)

                    if tweets is not None:
                        logger.info("  -> @%s: %d tweets found", username, len(tweets))
                        consecutive_failures = 0
                        parsed = [item for item in (self._parse_tweet(t, username) for t in tweets) if item]
                        async with lock:
                            all_items.extend(parsed)
                    else:
                        consecutive_failures += 1
                        if not is_retry:
                            async with lock:
                                failed_users.append((username, context_idx))

            # Round-robin assign users to context queues
            queues: list[list[str]] = [[] for _ in range(num_contexts)]
            for i, username in enumerate(users):
                queues[i % num_contexts].append(username)

            # First pass — all queues in parallel
            await asyncio.gather(*[process_queue(i, q) for i, q in enumerate(queues)])

            # Retry failed users with a different context
            if failed_users:
                logger.info("Retrying %d failed Twitter accounts with alternate cookies", len(failed_users))
                await asyncio.sleep(20)
                retry_queues: list[list[str]] = [[] for _ in range(num_contexts)]
                for username, original_idx in failed_users:
                    new_idx = (original_idx + 1) % num_contexts if num_contexts >= 2 else 0
                    retry_queues[new_idx].append(username)

                await asyncio.gather(*[
                    process_queue(i, q, is_retry=True)
                    for i, q in enumerate(retry_queues)
                    if q
                ])

            for ctx in contexts:
                await ctx.close()
            await browser.close()

        logger.info("Fetched %d tweets via Playwright.", len(all_items))
        return all_items

    async def _scrape_user(self, ctx, username: str, since: datetime) -> Optional[list[dict]]:
        """Scrape a single user's tweets via GraphQL interception."""
        page = await ctx.new_page()
        graphql_tweets: list[dict] = []

        async def handle_response(response):
            if "UserTweets" not in response.url and "UserByScreenName" not in response.url:
                return
            try:
                data = await response.json()

                def extract_tweets(obj):
                    if isinstance(obj, dict):
                        if obj.get("rest_id") and obj.get("legacy"):
                            legacy = obj["legacy"]
                            media_entities = (
                                legacy.get("extended_entities", {}).get("media", [])
                                or legacy.get("entities", {}).get("media", [])
                            )
                            images = [
                                m["media_url_https"]
                                for m in media_entities
                                if m.get("type") == "photo" and m.get("media_url_https")
                            ]
                            tweet = {
                                "tweet_id": obj["rest_id"],
                                "text": legacy.get("full_text", ""),
                                "datetime_raw": legacy.get("created_at", ""),
                                "is_retweet": (
                                    "retweeted_status_result" in obj.get("core", {})
                                    or "retweeted_status_id_str" in legacy
                                ),
                                "images": images,
                            }
                            try:
                                dt = datetime.strptime(tweet["datetime_raw"], "%a %b %d %H:%M:%S %z %Y")
                                tweet["datetime"] = dt.isoformat()
                            except (ValueError, TypeError):
                                tweet["datetime"] = tweet["datetime_raw"]
                            graphql_tweets.append(tweet)
                        for v in obj.values():
                            extract_tweets(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            extract_tweets(item)

                extract_tweets(data)
            except Exception as exc:
                logger.debug("GraphQL parse error: %s", exc)

        page.on("response", handle_response)

        # Block heavy resources
        async def route_handler(route):
            if route.request.resource_type in ("media", "image", "video"):
                await route.abort()
            else:
                url = route.request.url.lower()
                if any(k in url for k in ("google-analytics", "doubleclick", "scribe.twitter.com")):
                    await route.abort()
                else:
                    await route.continue_()

        await page.route("**/*", route_handler)

        try:
            await asyncio.sleep(random.uniform(2, 4))

            for attempt in range(3):
                if attempt > 0:
                    await asyncio.sleep(random.uniform(5, 10))
                try:
                    await page.goto(
                        f"https://x.com/{username}",
                        wait_until="domcontentloaded",
                        timeout=25000,
                    )
                    break
                except Exception as exc:
                    if "Timeout" in str(exc):
                        logger.debug("Page load slow (attempt %d/3)", attempt + 1)
                        if attempt == 2:
                            break
                    else:
                        if attempt == 2:
                            raise
                        logger.debug("Page visit error (attempt %d/3): %s", attempt + 1, exc)

            await asyncio.sleep(5)
            start_time = asyncio.get_event_loop().time()

            # Quick diagnostic: check if page requires login
            body_text = await page.evaluate("document.body ? document.body.innerText : ''")
            if body_text and any(k in body_text.lower() for k in ("log in", "sign up", "create account")):
                logger.warning("  -> @%s page shows login gate — cookie may be invalid", username)

            while (asyncio.get_event_loop().time() - start_time) < 60:
                if graphql_tweets:
                    result = []
                    seen = set()
                    for t in graphql_tweets:
                        uid = t.get("tweet_id") or hashlib.md5(t["text"].encode()).hexdigest()
                        if uid in seen:
                            continue
                        seen.add(uid)
                        try:
                            tweet_time = datetime.fromisoformat(t["datetime"])
                            if tweet_time < since:
                                continue
                        except Exception:
                            continue
                        result.append(t)

                    if result:
                        logger.info("  -> @%s: %d tweets within time window", username, len(result))
                        return result[: self.twitter_config.fetch_limit]
                    logger.info("  -> @%s: intercepted %d tweets but all outside time window", username, len(graphql_tweets))
                    return []

                # Check for error pages
                body_text = await page.evaluate("document.body ? document.body.innerText : ''")
                if body_text and any(
                    kw in body_text
                    for kw in ("Retry", "Something went wrong", "出错了", "重新加载")
                ):
                    await page.reload(wait_until="load", timeout=30000)
                    await asyncio.sleep(5)

                # Simulate human browsing
                await page.mouse.move(random.randint(100, 600), random.randint(100, 600))
                await page.evaluate(f"window.scrollBy(0, {random.randint(300, 700)})")
                await asyncio.sleep(random.uniform(2, 4))

                at_bottom = await page.evaluate(
                    "window.innerHeight + window.scrollY >= document.body.scrollHeight"
                )
                if at_bottom and (asyncio.get_event_loop().time() - start_time) > 20:
                    break

            if not graphql_tweets:
                logger.warning("  -> @%s: no GraphQL data intercepted (cookie or page issue)", username)
                return None
            return []

        except Exception as exc:
            logger.warning("Failed to scrape @%s: %s", username, exc)
            return None
        finally:
            await page.close()

    def _parse_tweet(self, tweet: dict, username: str) -> Optional[ContentItem]:
        """Convert raw tweet dict to Horizon ContentItem."""
        try:
            tweet_id = str(tweet.get("tweet_id", ""))
            if not tweet_id:
                return None

            text = tweet.get("text", "")
            if not text:
                return None

            created_at_raw = tweet.get("datetime", "")
            try:
                published_at = datetime.fromisoformat(created_at_raw)
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return None

            title_body = text[:50].replace("\n", " ").strip()
            if len(text) > 50:
                title_body += "..."

            return ContentItem(
                id=self._generate_id(SourceType.TWITTER.value, "tweet", tweet_id),
                source_type=SourceType.TWITTER,
                title=f"@{username}: {title_body}",
                url=f"https://x.com/{username}/status/{tweet_id}",
                content=text,
                author=username,
                published_at=published_at,
                metadata={
                    "tweet_id": tweet_id,
                    "is_retweet": tweet.get("is_retweet", False),
                    "images": tweet.get("images", []),
                },
            )
        except Exception as exc:
            logger.debug("Failed to parse tweet: %s", exc)
            return None
