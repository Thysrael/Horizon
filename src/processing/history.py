"""Small, read-only BM25 search over Horizon's Markdown digests."""

import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import html
import logging
import math
from pathlib import Path
import re
from typing import Any
from urllib.parse import urldefrag

logger = logging.getLogger(__name__)

_FILENAME = re.compile(r"^horizon-(\d{4}-\d{2}-\d{2})(?:-.*)?\.md$")
# Older digests use H2 for news; Profile-grouped digests use H3.
_ITEM = re.compile(
    r"^#{2,3} \[((?:\\.|[^\\\]])+)\]\((https?://\S+)\)[^\n]*\n",
    re.MULTILINE,
)
_TAGS = re.compile(r"^\*\*(?:Tags|标签)\*\*[:：]\s*(.*)$", re.MULTILINE)
_WORDS = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*[+#]*|[\u3400-\u9fff]+")
_STOP_WORDS = set("a an and are as at be by for from in is it of on or the to was with".split())


def _plain_text(text: str) -> str:
    text = re.sub(r"\\([\\`*_{}\[\]<>()#+!|])", r"\1", text)
    return html.unescape(text).replace("`", "").strip()


def _tokenize(text: str) -> list[str]:
    """Use Latin words and overlapping Chinese bigrams, without a segmenter."""
    terms = []
    for word in _WORDS.findall(text.casefold()):
        if "\u3400" <= word[0] <= "\u9fff" and len(word) > 1:
            terms.extend(word[index:index + 2] for index in range(len(word) - 1))
        elif word not in _STOP_WORDS:
            terms.append(word)
    return terms


def _url_key(url: str) -> str:
    return urldefrag(url)[0].rstrip("/")


@dataclass(frozen=True)
class HistoryEntry:
    title: str
    url: str
    summary: str
    digest_date: date
    filename: str
    terms: Counter[str]


def _read_entries(directory: Path) -> list[HistoryEntry]:
    entries = []
    for path in sorted(directory.glob("horizon-*.md")):
        filename = _FILENAME.fullmatch(path.name)
        if not filename:
            continue
        try:
            digest_date = date.fromisoformat(filename[1])
        except ValueError:
            continue
        try:
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            logger.warning("Could not read history file %s: %s", path.name, exc)
            continue

        headings = list(_ITEM.finditer(markdown))
        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
            body = markdown[heading.end():end].split("\n---", 1)[0].strip()
            summary = re.split(r"\n\s*\n", body, maxsplit=1)[0]
            # Only the leading main summary is evidence. Exclude background,
            # previous history callbacks, comments, and reference lists.
            if summary.startswith(("#", "<", "*")) or re.match(r"^[a-z_]+ · ", summary):
                summary = ""
            title, url = _plain_text(heading[1]), html.unescape(heading[2])
            summary = _plain_text(summary)
            tags = " ".join(_TAGS.findall(body))
            terms = Counter(_tokenize(f"{title} {title} {summary} {tags}"))
            entries.append(HistoryEntry(title, url, summary, digest_date, path.name, terms))
    return entries


def _rank(entries: list[HistoryEntry], query: str) -> list[HistoryEntry]:
    """BM25 with k1=1.5, b=0.75; dates break equal-score ties."""
    terms = set(_tokenize(query))
    if not entries or not terms:
        return []
    lengths = [sum(entry.terms.values()) for entry in entries]
    average_length = sum(lengths) / len(entries) or 1
    idf = {}
    for term in terms:
        frequency = sum(term in entry.terms for entry in entries)
        idf[term] = math.log(1 + (len(entries) - frequency + 0.5) / (frequency + 0.5))

    scored = []
    for entry, length in zip(entries, lengths):
        score = 0.0
        normalization = 1.5 * (0.25 + 0.75 * length / average_length)
        for term in terms:
            frequency = entry.terms[term]
            score += idf[term] * frequency * 2.5 / (frequency + normalization)
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda pair: (pair[0], pair[1].digest_date), reverse=True)
    return [entry for _, entry in scored]


def reported_urls_before(directory: Path, before: date) -> set[str]:
    """Return raw URLs already published in digests dated before `before`.

    Used to suppress items a previous digest already covered. Per-source windows
    (e.g. GitHub releases looking back 30h) intentionally span more than one day,
    so without this filter the same release would appear in consecutive digests.
    Digests dated `before` or later are ignored: a same-day rerun should be able
    to regenerate the full digest.

    URLs are returned as written in the digest; callers apply their own
    normalization so the comparison matches their dedup key.
    """
    return {
        entry.url
        for entry in _read_entries(directory)
        if entry.digest_date < before
    }


class HistorySearchTool:
    name = "history_search"

    def __init__(self, summaries_dir: Path | None = None):
        self.summaries_dir = summaries_dir
        self._entries: list[HistoryEntry] | None = None
        self._load_lock = asyncio.Lock()

    async def execute(
        self,
        arguments: dict[str, Any],
        *,
        before: date | None = None,
        exclude_url: str = "",
    ) -> list[dict[str, str]]:
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("history_search requires a non-empty query")
        days = arguments.get("days", 90)
        if type(days) is not int or not 1 <= days <= 365:
            raise ValueError("history_search days must be an integer from 1 to 365")
        if self.summaries_dir is None:
            return []

        async with self._load_lock:
            if self._entries is None:
                self._entries = await asyncio.to_thread(_read_entries, self.summaries_dir)

        today = datetime.now(timezone.utc).date()
        before = min(before, today) if before else today
        since = before - timedelta(days=days)
        entries = [entry for entry in self._entries if since <= entry.digest_date < before]
        ranked = await asyncio.to_thread(_rank, entries, query)

        results = []
        seen = {_url_key(exclude_url)}
        for entry in ranked:
            key = _url_key(entry.url)
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "title": f"{entry.digest_date.isoformat()} — {entry.title}",
                "url": entry.url,
                "text": (
                    f"Horizon archive: {entry.filename}. "
                    "Date is the digest date, not a verified event date.\n"
                    f"Archived summary: {entry.summary[:500] or entry.title}"
                ),
            })
            if len(results) == 3:
                break
        return results
