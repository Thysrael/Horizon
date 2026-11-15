"""Podcast RSS discovery with explicitly linked, public written transcripts.

Show notes and audio enclosures are never used as transcript substitutes. This
source does not run speech recognition or make model calls.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
from xml.etree import ElementTree

import feedparser
import httpx
from dateutil.parser import isoparse

from .base import BaseScraper, FetchResult
from .rss import RSS_USER_AGENT
from ..models import ContentItem, PodcastSourceConfig, SourceType
from ..url_security import UnsafeURLError, validate_public_http_url

PODCAST_NAMESPACES = {
    "https://podcastindex.org/namespace/1.0",
    "https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md",
}
TRANSCRIPT_TYPES = {"text/plain", "text/vtt", "application/x-subrip", "text/srt", "text/html"}
MAX_FEED_BYTES = 8 * 1024 * 1024
MAX_TRANSCRIPT_BYTES = 4 * 1024 * 1024
MAX_CONCURRENT_FEEDS = 3
MAX_TRANSCRIPT_ALTERNATIVES = 3
_TIMESTAMP = r"(?:\d{2,}:)?\d{2}:\d{2}[.,]\d{3}"
_CUE = re.compile(rf"^({_TIMESTAMP})\s+-->\s+({_TIMESTAMP})(?:\s+.*)?$")


class _NoDoctypeBuilder(ElementTree.TreeBuilder):
    """Reject DTDs at the XML parser boundary, including non-UTF-8 feeds."""

    def doctype(self, name, pubid, system):
        raise ValueError("Podcast feeds may not contain DTD/entity declarations")


async def _read_public_resource(
    client: httpx.AsyncClient, url: str, limit: int
) -> tuple[bytes, str]:
    """Read a bounded response while validating every redirect destination."""
    for redirect in range(6):
        await validate_public_http_url(url)
        async with client.stream(
            "GET", url, follow_redirects=False, timeout=20.0,
            headers={"User-Agent": RSS_USER_AGENT},
        ) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location or redirect == 5:
                    raise UnsafeURLError("Missing redirect location or too many redirects")
                url = urljoin(url, location)
                continue
            response.raise_for_status()
            length = response.headers.get("content-length", "")
            if length.isdigit() and int(length) > limit:
                raise ValueError("Response exceeds byte limit")
            data = bytearray()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > limit:
                    raise ValueError("Response exceeds byte limit")
            return bytes(data), str(response.url)
    raise UnsafeURLError("Too many redirects")


def _caption_text(value: str) -> str:
    """Keep cue positions and speakers, dropping caption-only markup."""
    cues = []
    for block in re.split(r"\n\s*\n", value.replace("\r\n", "\n").replace("\r", "\n")):
        lines = block.strip().splitlines()
        if not lines or lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue
        for index, line in enumerate(lines):
            match = _CUE.fullmatch(line.strip())
            if not match:
                if "-->" in line:
                    raise ValueError("Transcript contains a malformed caption timestamp")
                continue
            content = " ".join(lines[index + 1:]).strip()
            content = re.sub(r"<v(?:\.[^\s>]+)?\s+([^>]+)>", r"\1: ", content)
            content = html.unescape(re.sub(r"<[^>]+>", "", content)).strip()
            if content:
                cues.append(f"[{match.group(1).replace(',', '.')}] {content}")
            break
    if not cues:
        raise ValueError("Transcript contains no valid caption cues")
    return "\n".join(cues)


async def _transcript_text(data: bytes, media_type: str, max_chars: int) -> str:
    # UTF-8 is required by the supported Podcasting 2.0 transcript formats.
    text = data.decode("utf-8-sig").strip()
    if media_type == "text/html":
        import trafilatura
        text = await asyncio.to_thread(
            trafilatura.extract, text, favor_recall=True,
            include_comments=False, include_tables=False,
        ) or ""
    elif media_type in {"text/vtt", "application/x-subrip", "text/srt"}:
        text = _caption_text(text)
    elif re.search(r"<(?:!doctype|html|head|body)\b", text[:1000], re.I):
        raise ValueError("Expected a plain transcript, received an HTML page")
    text = text.strip()
    if not text:
        raise ValueError("Transcript is empty")
    if len(text) > max_chars:
        raise ValueError("Transcript exceeds max_transcript_chars; no partial text accepted")
    return text


def _published_at(entry: dict) -> datetime:
    """Require an original publication time with a known UTC offset."""
    raw = entry.get("published", "")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Missing original publication timestamp")
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        parsed = isoparse(raw)
    # RFC 2822 -0000 expresses UTC without a known local timezone.
    if parsed.tzinfo is None and raw.rstrip().endswith("-0000"):
        parsed = parsed.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        raise ValueError("Original publication timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def _transcript_links(element: ElementTree.Element) -> list[tuple[str, str]]:
    links = []
    for child in element:
        if child.tag not in {f"{{{namespace}}}transcript" for namespace in PODCAST_NAMESPACES}:
            continue
        media_type = child.get("type", "").split(";", 1)[0].strip().lower()
        url = child.get("url", "").strip()
        if url and media_type in TRANSCRIPT_TYPES and (url, media_type) not in links:
            links.append((url, media_type))
    return links[:MAX_TRANSCRIPT_ALTERNATIVES]


class PodcastScraper(BaseScraper):
    """Collect RSS episodes that have a supported public transcript link."""

    def __init__(self, sources: list[PodcastSourceConfig], http_client: httpx.AsyncClient):
        super().__init__({"sources": sources}, http_client)

    async def fetch(self, since: datetime) -> FetchResult:
        if since.tzinfo is None:
            raise ValueError("Podcast fetch window must be timezone-aware")
        until = datetime.now(timezone.utc)
        slots = asyncio.Semaphore(MAX_CONCURRENT_FEEDS)

        async def fetch_source(source: PodcastSourceConfig) -> FetchResult:
            async with slots:
                try:
                    return await self._fetch_feed(source, since, until)
                except Exception as exc:
                    result = FetchResult()
                    # Do not expose publisher URL query parameters in diagnostics.
                    result.failures[source.name] = f"{type(exc).__name__}: podcast feed unavailable or invalid"
                    return result

        results = await asyncio.gather(*(
            fetch_source(source) for source in self.config["sources"] if source.enabled
        ))
        combined = FetchResult()
        for result in results:
            combined.items.extend(result.items)
            combined.failures.update(result.failures)
            combined.successful += result.successful
        return combined

    async def _fetch_feed(
        self, source: PodcastSourceConfig, since: datetime, until: datetime
    ) -> FetchResult:
        data, feed_url = await _read_public_resource(self.client, str(source.url), MAX_FEED_BYTES)
        root = ElementTree.fromstring(
            data, parser=ElementTree.XMLParser(target=_NoDoctypeBuilder())
        )
        if root.tag != "rss":
            raise ValueError("Podcast transcript discovery requires an RSS feed")
        elements = root.findall("./channel/item")
        feed = feedparser.parse(data)
        if len(elements) != len(feed.entries):
            raise ValueError("RSS entries could not be matched to transcript declarations")

        result = FetchResult()
        eligible = []
        seen = set()
        for ordinal, (entry, element) in enumerate(zip(feed.entries, elements), 1):
            label = f"{source.name}/entry:{ordinal}"
            try:
                published_at = _published_at(entry)
            except (ValueError, TypeError, OverflowError):
                result.failures[label] = "ValueError: missing or ambiguous original publication timestamp"
                continue
            if not since <= published_at < until:
                continue
            native_id = str(entry.get("id") or entry.get("link") or "")
            if not native_id:
                result.failures[label] = "ValueError: missing episode GUID and URL"
                continue
            if native_id in seen:
                continue
            seen.add(native_id)
            eligible.append((published_at, ordinal, entry, element, native_id))

        # Some feeds are not newest-first. Apply the per-run cap after sorting.
        eligible.sort(key=lambda value: value[0], reverse=True)
        for published_at, ordinal, entry, element, native_id in eligible[:source.max_items]:
            label = f"{source.name}/entry:{ordinal}"
            links = _transcript_links(element)
            if not links:
                result.failures[label] = "ValueError: no supported public transcript declaration"
                continue
            failures = []
            for transcript_url, media_type in links:
                try:
                    transcript_url = urljoin(feed_url, transcript_url)
                    body, final_url = await _read_public_resource(
                        self.client, transcript_url, MAX_TRANSCRIPT_BYTES
                    )
                    content = await _transcript_text(body, media_type, source.max_transcript_chars)
                    identity = hashlib.sha256(
                        f"{source.url}\n{native_id}".encode("utf-8")
                    ).hexdigest()[:24]
                    item = ContentItem(
                        id=self._generate_id("podcast", "episode", identity),
                        source_type=SourceType.PODCAST,
                        title=entry.get("title", "Untitled episode"),
                        url=entry.get("link") or final_url,
                        content=content,
                        author=entry.get("author") or feed.feed.get("author") or source.name,
                        published_at=published_at,
                        profile=source.profile,
                        metadata={
                            "content_kind": "podcast_transcript",
                            "feed_name": source.name,
                            "category": source.category,
                            "podcast": {
                                "feed_name": source.name,
                                "guid": native_id,
                                "transcript_url": final_url,
                                "transcript_format": media_type,
                                "transcript_status": "complete",
                            },
                        },
                    )
                except Exception as exc:
                    # Alternative formats can recover a failed first resource.
                    failures.append(type(exc).__name__)
                    continue
                result.items.append(item)
                break
            else:
                result.failures[label] = (
                    f"{', '.join(failures)}: public transcript unavailable, invalid or over configured limit"
                )
        result.successful = int(bool(result.items) or not result.failures)
        return result
