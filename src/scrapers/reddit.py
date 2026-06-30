"""Reddit scraper implementation."""

import asyncio
import calendar
import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, List, Optional, cast

import feedparser
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..models import (
    ContentItem,
    RedditConfig,
    RedditSubredditConfig,
    RedditUserConfig,
    SourceType,
)

logger = logging.getLogger(__name__)

REDDIT_BASE = "https://www.reddit.com"
OLD_REDDIT_BASE = "https://old.reddit.com"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)
REDDIT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{REDDIT_BASE}/",
}
MAX_COMMENT_CONCURRENCY = 2


class RedditBlockedError(Exception):
    """Raised when Reddit blocks an unauthenticated JSON listing request."""


class RedditScraper(BaseScraper):
    """Scraper for Reddit posts and comments."""

    def __init__(self, config: RedditConfig, http_client: httpx.AsyncClient):
        super().__init__(config.model_dump(), http_client)
        self.reddit_config = config
        self._comment_semaphore = asyncio.Semaphore(MAX_COMMENT_CONCURRENCY)

    async def fetch(self, since: datetime) -> List[ContentItem]:
        if not self.config.get("enabled", True):
            return []

        items = []
        for sub_cfg in self.reddit_config.subreddits:
            if sub_cfg.enabled:
                try:
                    items.extend(await self._fetch_subreddit(sub_cfg, since))
                except Exception as e:
                    logger.warning("Error fetching Reddit source: %s", e)

        for user_cfg in self.reddit_config.users:
            if user_cfg.enabled:
                try:
                    items.extend(await self._fetch_user(user_cfg, since))
                except Exception as e:
                    logger.warning("Error fetching Reddit source: %s", e)

        return items

    async def _fetch_subreddit(
        self, cfg: RedditSubredditConfig, since: datetime
    ) -> List[ContentItem]:
        html_items = await self._fetch_subreddit_html(cfg, since)
        if html_items:
            return html_items

        logger.warning(
            "Reddit old HTML returned no posts for r/%s; falling back to JSON",
            cfg.subreddit,
        )
        params: dict[str, Any] = {"limit": min(cfg.fetch_limit, 100), "raw_json": 1}
        if cfg.sort in ("top", "controversial"):
            params["t"] = cfg.time_filter

        url = f"{REDDIT_BASE}/r/{cfg.subreddit}/{cfg.sort}.json"
        try:
            data = await self._reddit_get(url, params)
        except RedditBlockedError:
            logger.warning(
                "Reddit blocked JSON listing for r/%s; falling back to RSS",
                cfg.subreddit,
            )
            return await self._fetch_subreddit_rss(cfg, since)
        if not data:
            return []

        posts = [
            child["data"]
            for child in data.get("data", {}).get("children", [])
            if child.get("kind") == "t3"
        ]
        return await self._process_posts(
            posts, since, "subreddit", cfg.subreddit, cfg.min_score, cfg.category
        )

    async def _fetch_subreddit_rss(
        self, cfg: RedditSubredditConfig, since: datetime
    ) -> List[ContentItem]:
        rss_url = f"{REDDIT_BASE}/r/{cfg.subreddit}/{cfg.sort}/.rss"

        try:
            response = await self.client.get(
                rss_url,
                headers={
                    **REDDIT_HEADERS,
                    "Accept": "application/atom+xml,application/xml,text/xml,*/*",
                },
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("Reddit RSS fallback failed for r/%s: %s", cfg.subreddit, e)
            return []

        feed = feedparser.parse(response.text)
        items = []
        for entry in feed.entries[: cfg.fetch_limit]:
            published_at = self._parse_rss_date(entry)
            if not published_at or published_at < since:
                continue

            entry_id = str(
                entry.get("id") or entry.get("link") or entry.get("title", "")
            )
            title = str(entry.get("title") or "Untitled")
            link = str(entry.get("link") or f"{REDDIT_BASE}/r/{cfg.subreddit}/")
            content = self._strip_html(str(entry.get("summary") or ""))

            items.append(
                ContentItem(
                    id=self._generate_id("reddit", "subreddit-rss", entry_id),
                    source_type=SourceType.REDDIT,
                    title=title,
                    url=cast(Any, link),
                    content=content,
                    author=str(entry.get("author") or "unknown"),
                    published_at=published_at,
                    metadata={
                        "score": None,
                        "upvote_ratio": None,
                        "num_comments": None,
                        "subreddit": cfg.subreddit,
                        "is_self": None,
                        "flair": None,
                        "discussion_url": link,
                        "fallback": "rss",
                        **({"category": cfg.category} if cfg.category else {}),
                    },
                )
            )
        return items

    async def _fetch_subreddit_html(
        self, cfg: RedditSubredditConfig, since: datetime
    ) -> List[ContentItem]:
        url = f"{OLD_REDDIT_BASE}/r/{cfg.subreddit}/{cfg.sort}/"
        params: dict[str, Any] = {"limit": min(cfg.fetch_limit, 100)}
        if cfg.sort in ("top", "controversial"):
            params["t"] = cfg.time_filter

        try:
            response = await self.client.get(
                url,
                params=params,
                headers={
                    **REDDIT_HEADERS,
                    "Accept": "text/html,application/xhtml+xml,*/*",
                },
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(
                "Reddit old HTML request failed for r/%s: %s", cfg.subreddit, e
            )
            return []

        posts = self._parse_old_reddit_posts(response.text, cfg)
        return await self._process_posts(
            posts, since, "subreddit-html", cfg.subreddit, cfg.min_score, cfg.category
        )

    def _parse_old_reddit_posts(
        self, html: str, cfg: RedditSubredditConfig
    ) -> List[dict]:
        soup = BeautifulSoup(html, "html.parser")
        posts = []
        for thing in soup.select("div.thing.link[data-fullname]")[: cfg.fetch_limit]:
            fullname = str(thing.get("data-fullname") or "")
            post_id = fullname.removeprefix("t3_")
            title_el = thing.select_one("a.title")
            if not post_id or not title_el:
                continue

            permalink = str(thing.get("data-permalink") or "")
            if permalink.startswith(REDDIT_BASE):
                permalink = permalink.removeprefix(REDDIT_BASE)
            if not permalink.startswith("/"):
                permalink = f"/r/{cfg.subreddit}/comments/{post_id}/"

            url = str(thing.get("data-url") or "")
            classes = thing.get("class") or []
            is_self = isinstance(classes, list) and "self" in classes or not url
            selftext = ""
            body_el = thing.select_one("div.expando div.usertext-body div.md")
            if body_el:
                selftext = body_el.get_text("\n", strip=True)

            posts.append(
                {
                    "id": post_id,
                    "title": title_el.get_text(" ", strip=True),
                    "is_self": is_self,
                    "subreddit": str(thing.get("data-subreddit") or cfg.subreddit),
                    "permalink": permalink,
                    "author": str(thing.get("data-author") or "unknown"),
                    "created_utc": self._parse_old_reddit_timestamp(thing),
                    "score": self._parse_int(thing.get("data-score"), default=0),
                    "upvote_ratio": None,
                    "num_comments": self._parse_comment_count(thing),
                    "selftext": selftext,
                    "url": url or f"{REDDIT_BASE}{permalink}",
                    "link_flair_text": self._parse_flair(thing),
                }
            )
        return posts

    @staticmethod
    def _parse_old_reddit_timestamp(thing: Any) -> float:
        timestamp = thing.get("data-timestamp")
        try:
            return int(str(timestamp)) / 1000
        except (TypeError, ValueError):
            pass

        time_el = thing.select_one("time[datetime]")
        if time_el and time_el.get("datetime"):
            try:
                parsed = datetime.fromisoformat(
                    str(time_el["datetime"]).replace("Z", "+00:00")
                )
                return parsed.timestamp()
            except ValueError:
                pass
        return 0

    @staticmethod
    def _parse_int(value: Any, default: int = 0) -> int:
        try:
            return int(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return default

    @classmethod
    def _parse_comment_count(cls, thing: Any) -> int:
        comments_el = thing.select_one("a.comments")
        if not comments_el:
            return 0
        match = re.search(r"[\d,]+", comments_el.get_text(" ", strip=True))
        return cls._parse_int(match.group(0), default=0) if match else 0

    @staticmethod
    def _parse_flair(thing: Any) -> Optional[str]:
        flair_el = thing.select_one("span.linkflairlabel")
        if not flair_el:
            return None
        flair = flair_el.get_text(" ", strip=True)
        return flair or None

    async def _fetch_user(
        self, cfg: RedditUserConfig, since: datetime
    ) -> List[ContentItem]:
        params: dict[str, Any] = {
            "limit": min(cfg.fetch_limit, 100),
            "sort": cfg.sort,
            "raw_json": 1,
        }
        url = f"{REDDIT_BASE}/user/{cfg.username}/submitted.json"
        data = await self._reddit_get(url, params)
        if not data:
            return []

        posts = [
            child["data"]
            for child in data.get("data", {}).get("children", [])
            if child.get("kind") == "t3"
        ]
        return await self._process_posts(
            posts, since, "user", cfg.username, min_score=0, category=cfg.category
        )

    async def _process_posts(
        self,
        posts: list,
        since: datetime,
        subtype: str,
        source_name: str,
        min_score: int,
        category: Optional[str] = None,
    ) -> List[ContentItem]:
        valid_posts = []
        comment_tasks = []
        fetch_comments = self.reddit_config.fetch_comments

        for post in posts:
            created = datetime.fromtimestamp(
                post.get("created_utc", 0), tz=timezone.utc
            )
            if created < since:
                continue
            if post.get("score", 0) < min_score:
                continue
            valid_posts.append(post)
            if fetch_comments > 0:
                comment_tasks.append(
                    self._fetch_comments(post.get("subreddit", ""), post["id"])
                )
            else:
                comment_tasks.append(self._empty_comments())

        if not valid_posts:
            return []

        all_comments = await asyncio.gather(*comment_tasks, return_exceptions=True)

        items = []
        for post, comments in zip(valid_posts, all_comments):
            if isinstance(comments, Exception):
                comments = []
            item = self._parse_post(post, cast(List[dict], comments), subtype, category)
            if item:
                items.append(item)
        return items

    @staticmethod
    async def _empty_comments() -> List[dict]:
        return []

    @staticmethod
    def _parse_rss_date(entry: dict) -> Optional[datetime]:
        for field in ["published", "updated", "created"]:
            parsed_field = f"{field}_parsed"
            if parsed_field in entry and entry[parsed_field]:
                return datetime.fromtimestamp(
                    calendar.timegm(entry[parsed_field]), tz=timezone.utc
                )
            if field in entry:
                try:
                    parsed = parsedate_to_datetime(entry[field])
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except Exception:
                    continue
        return None

    @staticmethod
    def _strip_html(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value)
        return re.sub(r"\s+", " ", text).strip()

    async def _fetch_comments(self, subreddit: str, post_id: str) -> List[dict]:
        fetch_limit = self.reddit_config.fetch_comments
        html_comments = await self._fetch_comments_html(subreddit, post_id, fetch_limit)
        if html_comments:
            return html_comments

        url = f"{REDDIT_BASE}/r/{subreddit}/comments/{post_id}.json"
        params = {"limit": fetch_limit, "depth": 1, "sort": "top", "raw_json": 1}

        async with self._comment_semaphore:
            data = await self._reddit_get(url, params)
        if not data or not isinstance(data, list) or len(data) < 2:
            return []

        comments = []
        for child in data[1].get("data", {}).get("children", []):
            if child.get("kind") != "t1":
                continue
            c = child["data"]
            if c.get("body") and not c.get("distinguished") == "moderator":
                comments.append(c)

        comments.sort(key=lambda c: c.get("score", 0), reverse=True)
        return comments[:fetch_limit]

    async def _fetch_comments_html(
        self, subreddit: str, post_id: str, fetch_limit: int
    ) -> List[dict]:
        url = f"{OLD_REDDIT_BASE}/r/{subreddit}/comments/{post_id}/"
        params = {"limit": fetch_limit, "sort": "top"}

        try:
            response = await self.client.get(
                url,
                params=params,
                headers={
                    **REDDIT_HEADERS,
                    "Accept": "text/html,application/xhtml+xml,*/*",
                },
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.info("Reddit old HTML comments failed for %s: %s", post_id, e)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        comments = []
        for comment_el in soup.select("div.comment[data-fullname]"):
            classes = comment_el.get("class") or []
            if isinstance(classes, list) and "deleted" in classes:
                continue
            body_el = comment_el.select_one("div.usertext-body div.md")
            if not body_el:
                continue
            body = body_el.get_text("\n", strip=True)
            if not body:
                continue
            comments.append(
                {
                    "author": str(comment_el.get("data-author") or "anon"),
                    "body": body,
                    "score": self._parse_int(comment_el.get("data-score"), default=0),
                }
            )

        comments.sort(key=lambda c: c.get("score", 0), reverse=True)
        return comments[:fetch_limit]

    def _parse_post(
        self, post: dict, comments: List[dict], subtype: str, category: Optional[str] = None
    ) -> Optional[ContentItem]:
        post_id = post["id"]
        title = post.get("title", "")
        is_self = post.get("is_self", False)
        subreddit = post.get("subreddit", "")
        discussion_url = f"https://www.reddit.com{post.get('permalink', '')}"

        # For link posts, use the external URL; for self posts, use the discussion URL
        url = discussion_url if is_self else post.get("url", discussion_url)

        author = post.get("author", "unknown")
        created = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)

        # Build content
        parts = []
        if post.get("selftext"):
            text = post["selftext"]
            if len(text) > 1500:
                text = text[:1497] + "..."
            parts.append(text)

        if comments:
            parts.append("\n--- Top Comments ---")
            for c in comments:
                commenter = c.get("author", "anon")
                body = c.get("body", "")
                body = body.strip()
                if len(body) > 500:
                    body = body[:497] + "..."
                score = c.get("score", 0)
                parts.append(f"[{commenter} ({score} pts)]: {body}")

        content = "\n\n".join(parts)

        return ContentItem(
            id=self._generate_id("reddit", subtype, post_id),
            source_type=SourceType.REDDIT,
            title=title,
            url=cast(Any, url),
            content=content,
            author=author,
            published_at=created,
            metadata={
                "score": post.get("score", 0),
                "upvote_ratio": post.get("upvote_ratio"),
                "num_comments": post.get("num_comments", 0),
                "subreddit": subreddit,
                "is_self": is_self,
                "flair": post.get("link_flair_text"),
                "discussion_url": discussion_url,
                **({"category": category} if category else {}),
            },
        )

    async def _reddit_get(self, url: str, params: dict) -> Optional[Any]:
        try:
            response = await self.client.get(
                url,
                params=params,
                headers=REDDIT_HEADERS,
                follow_redirects=True,
            )
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                logger.warning("Reddit rate limited, retrying after %ds", retry_after)
                await asyncio.sleep(retry_after)
                response = await self.client.get(
                    url,
                    params=params,
                    headers=REDDIT_HEADERS,
                    follow_redirects=True,
                )
            if response.status_code == 403 and "/comments/" in url:
                logger.info(
                    "Reddit blocked comments request for %s; continuing without comments",
                    url,
                )
                return None
            if response.status_code == 403:
                raise RedditBlockedError(url)
            response.raise_for_status()
            return response.json()
        except RedditBlockedError:
            raise
        except httpx.HTTPError as e:
            logger.warning("Reddit request failed for %s: %s", url, e)
            return None
