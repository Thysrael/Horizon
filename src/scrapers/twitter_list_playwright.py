"""X/Twitter List scraping helpers for the Playwright scraper."""

import asyncio
import logging
import random
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


async def scrape_list_timeline(ctx, list_id: str, since: datetime, fetch_limit: int) -> Optional[list[dict]]:
    """Scrape an X/Twitter List timeline via DOM extraction.

    Returns raw tweet dictionaries compatible with ``TwitterPlaywrightScraper._parse_tweet``.
    This module is intentionally isolated from the profile scraper so List support can be
    maintained or upstreamed with a minimal integration hook.
    """
    page = await ctx.new_page()
    all_tweets: list[dict] = []
    seen_ids: set[str] = set()

    async def route_handler(route):
        if route.request.resource_type in ("media", "image", "video", "font"):
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", route_handler)

    try:
        await page.goto(f"https://x.com/i/lists/{list_id}", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(6)

        for scroll_index in range(20):
            tweets = await page.evaluate(r"""
                () => {
                    const results = [];
                    const articles = document.querySelectorAll('article[data-testid="tweet"]');
                    articles.forEach(article => {
                        const link = article.querySelector('a[href*="/status/"]');
                        const textEl = article.querySelector('[data-testid="tweetText"]');
                        const timeEl = article.querySelector('time');
                        const href = link ? link.getAttribute('href') : '';
                        const match = href.match(/\/(\w+)\/status\/(\d+)/);
                        const username = match ? match[1] : '';
                        const tweetId = match ? match[2] : '';
                        const text = textEl ? textEl.innerText : '';
                        const timestamp = timeEl ? timeEl.getAttribute('datetime') : '';
                        if (tweetId && text) results.push({ username, tweetId, text, timestamp });
                    });
                    return results;
                }
            """)

            for tweet in tweets:
                tweet_id = tweet["tweetId"]
                if not tweet_id or tweet_id in seen_ids:
                    continue
                seen_ids.add(tweet_id)
                try:
                    published_at = datetime.fromisoformat(tweet["timestamp"].replace("Z", "+00:00"))
                except Exception:
                    continue
                if published_at < since:
                    continue
                all_tweets.append({
                    "tweet_id": tweet_id,
                    "text": tweet["text"],
                    "datetime": published_at.isoformat(),
                    "username": tweet.get("username", ""),
                })

            if len(all_tweets) >= fetch_limit * 10:
                break
            await page.evaluate("window.scrollBy(0, 1200)")
            await asyncio.sleep(random.uniform(2, 4))
            at_bottom = await page.evaluate(
                "window.innerHeight + window.scrollY >= document.body.scrollHeight - 500"
            )
            if at_bottom and scroll_index > 3:
                break

        logger.info("  -> List %s: %d tweets within window", list_id, len(all_tweets))
        return all_tweets[: fetch_limit * 10]

    except Exception as exc:
        logger.warning("Failed to scrape X/Twitter list %s: %s", list_id, exc)
        return None
    finally:
        await page.close()
