"""A normal podcast source reaches native AI processing and Markdown output."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from src.ai.analyzer import ContentAnalyzer
from src.ai.enricher import ContentEnricher
from src.ai.summarizer import DailySummarizer
from src.models import AIConfig, PodcastSourceConfig, SourceType
from src.processing.profiles import ProfileRegistry
from src.scrapers.podcast import PodcastScraper


@pytest.mark.parametrize("configured_languages,expected_language", [(None, "en"), (["zh"], "zh")])
def test_public_transcript_to_native_podcast_digest(monkeypatch, configured_languages, expected_language):
    # Synthetic material is longer than the built-in 12,000-character chunk.
    opening = "Host: Describe your experiment. Guest: We tested a concrete hypothesis.\n"
    closing = "Guest: The copper telescope experiment changed our conclusion."
    transcript = opening * 190 + closing
    feed = """<rss version="2.0" xmlns:podcast="https://podcastindex.org/namespace/1.0">
      <channel><title>Experimental Conversations</title><item>
        <guid isPermaLink="false">experiment-one</guid>
        <title>A conversation about experiments</title>
        <link>https://example.com/episodes/one</link>
        <pubDate>Fri, 24 Apr 2026 12:00:00 GMT</pubDate>
        <description>Promotional show notes do not contain the final finding.</description>
        <enclosure url="https://example.com/audio.mp3" type="audio/mpeg" length="100"/>
        <podcast:transcript url="https://example.com/one.txt" type="text/plain"/>
      </item></channel></rss>"""
    http_requests, model_requests = [], []

    async def public_dns(_host, _port):
        return {"93.184.216.34"}

    monkeypatch.setattr("src.url_security._resolve_hostname", public_dns)

    def transport(request):
        http_requests.append(str(request.url))
        if request.url.path == "/feed.xml":
            return httpx.Response(200, text=feed)
        if request.url.path == "/one.txt":
            return httpx.Response(200, text=transcript)
        raise AssertionError(f"Unexpected request: {request.url}")

    class FakeClient:
        model = "offline-test-model"

        async def complete(self, **request):
            model_requests.append(request)
            system, user = request["system"], request["user"]
            if "Extract evidence notes" in system:
                source = user.split("\n", 1)[1]
                evidence = closing if closing in source else source[:50]
                return json.dumps({"points": [{"speaker": "Guest", "claim": evidence, "evidence": evidence}]})
            assert "copper telescope experiment" in user, "The closing insight must reach both AI stages"
            if "# Output contract" in system:
                return json.dumps({"score": 8.5, "reason": "Specific experimental evidence",
                                   "summary": "The copper telescope experiment changed the conclusion.",
                                   "tags": ["experiments"]})
            assert "# Target language" in system
            assert ("Simplified Chinese" in system) == (expected_language == "zh")
            content = (
                "嘉宾解释了实验如何检验原有假设。最后的铜望远镜实验改变了他们的结论。"
                if expected_language == "zh" else
                "The guest explains how experiments tested the initial hypothesis. "
                "The copper telescope experiment changed their conclusion."
            )
            return json.dumps({"title": "Experimental lessons", "blocks": [
                {"id": "summary", "title": "Reading brief", "content": content, "source_refs": []}
            ]})

    options = {"provider": "openai", "model": "offline-test-model", "api_key_env": "UNUSED_TEST_KEY"}
    if configured_languages is not None:
        options["languages"] = configured_languages
    ai = AIConfig.model_validate(options)
    assert ai.languages == [expected_language]
    source = PodcastSourceConfig(name="Experimental Conversations", url="https://example.com/feed.xml")
    assert source.profile == "podcast"  # No personal overrides or manual classification.
    profiles = ProfileRegistry.load(Path(__file__).resolve().parents[1] / "profiles", "tech-news")
    client = FakeClient()

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
            fetched = await PodcastScraper([source], http).fetch(datetime(2026, 4, 24, tzinfo=timezone.utc))
        assert fetched.status == "success"
        entry, = fetched.items
        assert entry.source_type == SourceType.PODCAST
        assert entry.content == transcript
        analyzed = await ContentAnalyzer(client, profiles).analyze_batch(fetched.items)
        assert entry.processing.classification.profile == "podcast"
        assert entry.processing.analysis.score == 8.5
        assert "copper telescope experiment" in entry.processing.analysis.summary
        enriched = await ContentEnricher(client, profiles, ai.languages).enrich_batch(analyzed)
        assert enriched.status == "success"
        assert entry.metadata["long_form"]["processed_chunks"] == 2
        return await DailySummarizer(profile_names=profiles.names).generate_summary(
            analyzed, "2026-04-25", total_fetched=1, language=expected_language
        )

    markdown = asyncio.run(run())
    expected_finding = "铜望远镜实验" if expected_language == "zh" else "copper telescope experiment"
    assert expected_finding in markdown
    assert "https://example.com/one.txt" in markdown
    assert "https://example.com/episodes/one" in markdown
    assert ("播客精读" if expected_language == "zh" else "Podcast") in markdown
    assert "Promotional show notes" not in markdown
    assert http_requests == ["https://example.com/feed.xml", "https://example.com/one.txt"]
    assert len(model_requests) == 4  # Two extraction calls, scoring, and one artifact; no tools or ASR.
