"""Podcast discovery tests use synthetic feeds/transcripts, never real audio."""

import asyncio
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import httpx
import pytest

from src.models import PodcastSourceConfig, SourceType
from src.scrapers.podcast import PodcastScraper, _caption_text, _read_public_resource

SINCE = datetime(2026, 4, 24, tzinfo=timezone.utc)
NAMESPACE = "https://podcastindex.org/namespace/1.0"


def episode(guid="one", *, date="Fri, 24 Apr 2026 12:00:00 GMT", links=None, extra=""):
    if links is None:
        links = [("https://example.com/one.txt", "text/plain")]
    declarations = "".join(
        f'<podcast:transcript url="{escape(url)}" type="{media_type}"/>'
        for url, media_type in links
    )
    return (
        f'<item><guid isPermaLink="false">{guid}</guid><title>Interview {guid}</title>'
        f'<link>https://example.com/{guid}</link><pubDate>{date}</pubDate>'
        f'<description>This is only a promotional show note.</description>'
        f'{declarations}{extra}</item>'
    )


def feed(*entries, namespace=NAMESPACE):
    return (
        f'<rss version="2.0" xmlns:podcast="{namespace}"><channel><title>Test show</title>'
        + "".join(entries) + '</channel></rss>'
    )


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    async def resolve(_host, _port):
        return {"93.184.216.34"}
    monkeypatch.setattr("src.url_security._resolve_hostname", resolve)


def collect(feed_text, transcripts=None, *, sources=None):
    requests = []
    transcripts = transcripts or {}
    def handler(request):
        requests.append(str(request.url))
        if request.url.path.endswith("feed.xml"):
            return httpx.Response(200, text=feed_text)
        response = transcripts.get(str(request.url))
        if isinstance(response, httpx.Response):
            return response
        if response is not None:
            return httpx.Response(200, content=response)
        return httpx.Response(404)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await PodcastScraper(sources or [PodcastSourceConfig(
                name="Test show", url="https://example.com/feed.xml"
            )], client).fetch(SINCE)
    return asyncio.run(run()), requests


def test_public_transcript_keeps_full_tail_and_original_identity():
    transcript = "Host: Tell us what happened.\n" * 500 + "Guest: The final lesson is important."
    first, requests = collect(feed(episode()), {"https://example.com/one.txt": transcript})
    second, _ = collect(feed(episode()), {"https://example.com/one.txt": transcript})
    assert first.status == "success"
    item = first.items[0]
    assert item.source_type == SourceType.PODCAST
    assert item.profile == "podcast"
    assert item.content == transcript
    assert item.id == second.items[0].id
    assert item.metadata["podcast"]["guid"] == "one"
    assert item.metadata["podcast"]["transcript_url"] == "https://example.com/one.txt"
    assert item.metadata["podcast"]["transcript_status"] == "complete"
    assert requests == ["https://example.com/feed.xml", "https://example.com/one.txt"]


def test_missing_or_foreign_namespace_never_uses_show_notes():
    for xml in [feed(episode(links=[])), feed(episode(), namespace="https://fake.example/ns")]:
        result, requests = collect(xml)
        assert result.items == []
        assert result.status == "failure"
        assert "no supported public transcript" in result.failures["Test show/entry:1"]
        assert len(requests) == 1


def test_official_namespace_alias_and_alternative_prefix():
    xml = feed(episode(), namespace="https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md")
    xml = xml.replace("xmlns:podcast", "xmlns:p").replace("podcast:transcript", "p:transcript")
    result, _ = collect(xml, {"https://example.com/one.txt": "Host: An available transcript."})
    assert len(result.items) == 1


def test_failed_first_format_recovers_with_next_link():
    xml = feed(episode(links=[
        ("https://example.com/fail.txt", "text/plain"),
        ("https://example.com/one.vtt", "text/vtt"),
    ]))
    result, requests = collect(xml, {"https://example.com/one.vtt":
        "WEBVTT\n\n00:01.000 --> 00:03.000\n<v Guest>Here is an example.</v>\n\n"
        "00:04.000 --> 00:06.000\nThe final takeaway.\n"})
    assert result.status == "success"
    assert "[00:01.000] Guest: Here is an example." in result.items[0].content
    assert result.items[0].content.endswith("The final takeaway.")
    assert len(requests) == 3


def test_rejects_missing_empty_malformed_and_oversized_transcripts_but_keeps_sibling():
    entries = [episode("valid"), episode("empty", links=[("https://example.com/empty.txt", "text/plain")]),
        episode("huge", links=[("https://example.com/huge.txt", "text/plain")]),
        episode("broken", links=[("https://example.com/broken.vtt", "text/vtt")])]
    result, _ = collect(feed(*entries), {
        "https://example.com/one.txt": "An actual interview transcript.",
        "https://example.com/empty.txt": " ",
        "https://example.com/huge.txt": "x" * 1001,
        "https://example.com/broken.vtt": "not captions",
    }, sources=[PodcastSourceConfig(name="Test show", url="https://example.com/feed.xml", max_transcript_chars=1000)])
    assert result.status == "partial_failure"
    assert [item.title for item in result.items] == ["Interview valid"]
    assert set(result.failures) == {"Test show/entry:2", "Test show/entry:3", "Test show/entry:4"}
    assert result.successful == 1


def test_newest_eligible_episode_cap_and_no_future_or_updated_timestamp_fallback():
    xml = feed(
        episode("old", date="Thu, 23 Apr 2026 12:00:00 GMT"),
        episode("first"),
        episode("latest", date="Fri, 24 Apr 2026 13:00:00 GMT"),
        episode("future", date="Fri, 24 Apr 2099 12:00:00 GMT"),
        episode("updated", date="bad", extra="<updated>2026-04-24T12:00:00Z</updated>"),
    )
    result, requests = collect(xml, {"https://example.com/one.txt": "An interview."}, sources=[
        PodcastSourceConfig(name="Test show", url="https://example.com/feed.xml", max_items=1)
    ])
    assert [item.title for item in result.items] == ["Interview latest"]
    assert "Test show/entry:5" in result.failures
    assert len(requests) == 2


def test_duplicate_guid_is_not_fetched_twice():
    result, requests = collect(feed(episode(), episode()), {"https://example.com/one.txt": "Interview."})
    assert len(result.items) == 1
    assert len(requests) == 2


def test_supported_html_is_declared_transcript_only(monkeypatch):
    seen = []
    def extract(value, **_kwargs):
        seen.append(value)
        return "Host: What changed?\nGuest: We redesigned the experiment."
    monkeypatch.setattr("trafilatura.extract", extract)
    xml = feed(episode(links=[("https://example.com/transcript.html", "text/html")]))
    result, requests = collect(xml, {"https://example.com/transcript.html": "<article>Interview</article>"})
    assert result.items[0].content.endswith("redesigned the experiment.")
    assert len(seen) == 1
    assert requests[-1].endswith("transcript.html")
    assert "https://example.com/one" not in requests


def test_plaintext_login_page_is_not_accepted_as_transcript():
    result, _ = collect(feed(episode()), {"https://example.com/one.txt": "<!DOCTYPE html><html>Log in</html>"})
    assert result.items == []
    assert result.failures


def test_private_redirect_is_rejected_before_request():
    result, requests = collect(feed(episode()), {
        "https://example.com/one.txt": httpx.Response(302, headers={"location": "http://localhost/secret"})
    })
    assert result.items == []
    assert "UnsafeURLError" in result.failures["Test show/entry:1"]
    assert not any("localhost" in request for request in requests)


def test_stream_byte_limit_and_content_length_limit():
    async def run(headers):
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, content=b"123456", headers=headers)
        )) as client:
            with pytest.raises(ValueError, match="byte limit"):
                await _read_public_resource(client, "https://example.com/t.txt", 5)
    asyncio.run(run({}))
    asyncio.run(run({"content-length": "6"}))


def test_srt_and_vtt_keep_timestamps_and_speaker_names():
    assert _caption_text("1\n00:00:01,500 --> 00:00:02,000\nAda: first point\n\n"
        "2\n00:00:03,000 --> 00:00:05,000\nA second line") == (
        "[00:00:01.500] Ada: first point\n[00:00:03.000] A second line"
    )


def test_disabled_and_old_only_feeds_are_empty_success():
    result, requests = collect(feed(episode(date="Thu, 23 Apr 2026 12:00:00 GMT")))
    assert result.status == "empty"
    assert result.successful == 1
    assert len(requests) == 1
    result, requests = collect("", sources=[PodcastSourceConfig(
        name="Disabled", url="https://example.com/feed.xml", enabled=False
    )])
    assert result.items == []
    assert requests == []


def test_malformed_later_caption_rejects_partial_transcript():
    transcript = "WEBVTT\n\n00:01.000 --> 00:02.000\nFirst point\n\nbad --> bad\nLost last point"
    result, _ = collect(feed(episode(links=[("https://example.com/one.vtt", "text/vtt")])), {
        "https://example.com/one.vtt": transcript
    })
    assert result.items == []
    assert result.status == "failure"


def test_fetch_failures_are_isolated_and_do_not_expose_query_tokens():
    requests = []
    def handler(request):
        requests.append(str(request.url))
        if request.url.host == "failed.example.com":
            return httpx.Response(403)
        if request.url.path == "/feed.xml":
            return httpx.Response(200, text=feed(episode()))
        return httpx.Response(200, text="A transcript from the healthy feed.")
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await PodcastScraper([
                PodcastSourceConfig(name="Blocked", url="https://failed.example.com/feed.xml?key=secret"),
                PodcastSourceConfig(name="Healthy", url="https://example.com/feed.xml"),
            ], client).fetch(SINCE)
    result = asyncio.run(run())
    assert result.status == "partial_failure"
    assert len(result.items) == 1
    assert set(result.failures) == {"Blocked"}
    assert "secret" not in str(result.failures)


def test_future_boundary_uses_fetch_start_time(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 24, 13, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("src.scrapers.podcast.datetime", Clock)
    result, _ = collect(feed(
        episode("start", date="Fri, 24 Apr 2026 00:00:00 GMT"),
        episode("end", date="Fri, 24 Apr 2026 13:00:00 GMT"),
    ), {"https://example.com/one.txt": "Transcript"})
    assert [item.title for item in result.items] == ["Interview start"]


def test_rejects_dtd_feed_without_fetching_transcripts():
    xml = '<!DOCTYPE rss [<!ENTITY e "unexpected">]>' + feed(episode())
    result, requests = collect(xml)
    assert result.items == []
    assert result.status == "failure"
    assert len(requests) == 1


def test_transcript_alternative_requests_are_bounded():
    links = [(f"https://example.com/{i}.txt", "text/plain") for i in range(8)]
    result, requests = collect(feed(episode(links=links)))
    assert result.status == "failure"
    assert len(requests) == 4  # One feed plus at most three declared alternatives.


@pytest.mark.parametrize("date", ["Fri, 24 Apr 2026 12:00:00", "2026-04-24T12:00:00"])
def test_timezone_unknown_publication_is_rejected(date):
    result, requests = collect(feed(episode(date=date)))
    assert result.items == []
    assert "ambiguous original publication" in result.failures["Test show/entry:1"]
    assert len(requests) == 1


@pytest.mark.parametrize("date", ["Fri, 24 Apr 2026 12:00:00 -0000", "2026-04-24T20:00:00+08:00"])
def test_explicit_utc_and_iso_offset_dates(date):
    result, _ = collect(feed(episode(date=date)), {"https://example.com/one.txt": "Transcript."})
    assert result.items[0].published_at == datetime(2026, 4, 24, 12, tzinfo=timezone.utc)


def test_utf16_dtd_cannot_bypass_xml_declaration_guard():
    xml = ('<?xml version="1.0" encoding="utf-16"?>'
        '<!DOCTYPE rss [<!ENTITY e "unexpected">]>' + feed(episode())).encode("utf-16")
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, content=xml)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await PodcastScraper([PodcastSourceConfig(
                name="Unsafe", url="https://example.com/feed.xml"
            )], client).fetch(SINCE)
    result = asyncio.run(run())
    assert result.status == "failure"
    assert result.items == []
    assert len(requests) == 1
