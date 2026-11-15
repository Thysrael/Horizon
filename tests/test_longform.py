"""Long transcript coverage, bounded calls and native pipeline regression tests."""

import asyncio
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ai.analyzer import ContentAnalyzer
from src.ai.enricher import ContentEnricher
from src.ai.longform import LongFormError, prepare_content, prepared_content
from src.ai.prompting.enrichment import item_context
from src.models import ContentItem, SourceType
from src.processing.profiles import LongFormContent, ProfileRegistry


BASE = ProfileRegistry.load(Path(__file__).resolve().parents[1] / "profiles", "tech-news")


def profile(*, chunk_chars=1000, max_chunks=8, budget=8000):
    original = BASE.get("tech-news")
    definition = original.definition.model_copy(deep=True)
    definition.content.long_form = LongFormContent(chunk_chars=chunk_chars, max_chunks=max_chunks)
    definition.content.analysis_max_chars = budget
    definition.content.enrichment_max_chars = budget
    definition.enrichment.blocks = [definition.enrichment.blocks[0]]
    definition.enrichment.blocks[0].tools = []
    return replace(original, definition=definition)


def item(text):
    return ContentItem(
        id="rss:episode:1", source_type=SourceType.RSS,
        profile="tech-news", title="A synthetic long interview",
        url="https://example.com/episode", content=text,
        published_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        metadata={"podcast": {"transcript_url": "https://example.com/transcript.txt"}},
    )


class FakeClient:
    model = "test-model"

    def __init__(self):
        self.requests = []

    async def complete(self, **kwargs):
        self.requests.append(kwargs)
        if "Extract evidence notes" in kwargs["system"]:
            source = kwargs["user"].split("\n", 1)[1]
            claim = "The closing finding matters" if "TAIL_FINDING" in source else "Opening context"
            evidence = "TAIL_FINDING" if "TAIL_FINDING" in source else source[:20]
            return json.dumps({"points": [{"claim": claim, "evidence": evidence}]})
        if "# Output contract" in kwargs["system"]:
            assert "closing finding" in kwargs["user"]
            return json.dumps({"score": 8, "reason": "A concrete finding", "summary": "A full interview"})
        assert "closing finding" in kwargs["user"]
        return json.dumps({"title": "Interview insights", "blocks": [
            {"id": "summary", "title": "Summary", "content": "The closing finding is useful.", "source_refs": []}
        ]})

    @property
    def extraction_calls(self):
        return [r for r in self.requests if "Extract evidence notes" in r["system"]]


def transcript():
    return "Opening evidence. " * 140 + "\n--- Top Comments ---\nTAIL_FINDING: late important point."


def test_every_character_including_tail_and_comment_marker_is_read():
    entry = item(transcript())
    selected = profile()
    client = FakeClient()
    notes = asyncio.run(prepare_content(entry, selected, client))
    calls = client.extraction_calls
    submitted = "".join(r["user"].split("\n", 1)[1] for r in calls)
    assert submitted == entry.content
    assert len(calls) == 3
    assert "closing finding" in notes
    assert len(notes) <= 8000
    assert entry.content == transcript()
    assert entry.metadata["long_form"]["processed_chunks"] == 3
    assert "closing finding" in item_context(entry, selected, True)
    assert "[Opening excerpt]" not in notes


def test_native_analysis_and_enrichment_reuse_complete_evidence_and_keep_source():
    selected = profile()
    registry = ProfileRegistry({"tech-news": selected}, "tech-news")
    entry = item(transcript())
    client = FakeClient()
    asyncio.run(ContentAnalyzer(client, registry)._analyze_item(entry))
    assert entry.processing.analysis.score == 8
    asyncio.run(ContentEnricher(client, registry, ["en"])._enrich_item(entry))
    assert len(client.extraction_calls) == 3
    artifact = entry.processing.artifacts["en"]
    assert artifact.sources[0].url == "https://example.com/transcript.txt"
    assert artifact.blocks[0].source_refs == ["transcript"]
    # Serialization preserves reusable stage state; no additional model call.
    restored = ContentItem.model_validate_json(entry.model_dump_json())
    asyncio.run(prepare_content(restored, selected, client))
    assert len(client.extraction_calls) == 3


def test_changed_source_profile_or_model_invalidates_cached_notes():
    entry = item("First evidence. " * 40)
    selected = profile()
    client = FakeClient()
    asyncio.run(prepare_content(entry, selected, client))
    first = entry.metadata["long_form"]["fingerprint"]
    entry.content += " Updated evidence."
    with pytest.raises(LongFormError, match="stale"):
        prepared_content(entry, selected)
    asyncio.run(prepare_content(entry, selected, client))
    second = entry.metadata["long_form"]["fingerprint"]
    client.model = "new-model"
    asyncio.run(prepare_content(entry, selected, client))
    third = entry.metadata["long_form"]["fingerprint"]
    changed = replace(selected, analysis_prompt="Different scoring policy")
    asyncio.run(prepare_content(entry, changed, client))
    assert len(client.extraction_calls) == 4
    assert len({first, second, third, entry.metadata["long_form"]["fingerprint"]}) == 4


@pytest.mark.parametrize("text,selected,match", [
    ("x" * 2100, profile(max_chunks=2), "configured limit"),
    ("x" * 2100, profile(budget=1000), "budget is too small"),
    ("", profile(), "empty"),
])
def test_budget_is_checked_before_any_paid_call(text, selected, match):
    client = FakeClient()
    with pytest.raises(LongFormError, match=match):
        asyncio.run(prepare_content(item(text), selected, client))
    assert client.requests == []


def test_failed_chunk_never_becomes_partial_analysis_and_retry_is_bounded():
    class FailingClient(FakeClient):
        async def complete(self, **kwargs):
            if "chunk 2/" in kwargs["user"]:
                self.requests.append(kwargs)
                return json.dumps({"points": [{"claim": "Fabricated", "evidence": "NOT_IN_SOURCE"}]})
            return await super().complete(**kwargs)

    selected = profile()
    registry = ProfileRegistry({"tech-news": selected}, "tech-news")
    entry = item(transcript())
    client = FailingClient()
    analyzed = asyncio.run(ContentAnalyzer(client, registry).analyze_batch([entry]))
    assert analyzed[0].processing.analysis.score is None
    assert entry.metadata["long_form"]["processed_chunks"] == 1
    assert entry.metadata["long_form"]["status"] == "partial"
    assert len(client.extraction_calls) == 3  # chunk 1 once, failed chunk twice
    with pytest.raises(LongFormError, match="not complete"):
        prepared_content(entry, selected)
    with pytest.raises(LongFormError, match="could not be verified"):
        asyncio.run(prepare_content(entry, selected, client))
    assert len(client.extraction_calls) == 3
    result = asyncio.run(ContentEnricher(client, registry, ["en"]).enrich_batch([entry]))
    assert result.failed_ids == [entry.id]
    assert entry.processing.artifacts == {}


def test_bad_cache_cannot_claim_full_coverage():
    selected = profile()
    entry = item(transcript())
    client = FakeClient()
    asyncio.run(prepare_content(entry, selected, client))
    entry.metadata["long_form"]["chunks"].pop()
    with pytest.raises(LongFormError, match="full source"):
        prepared_content(entry, selected)


def test_evidence_is_verified_again_when_reusing_cache():
    selected = profile()
    entry = item(transcript())
    asyncio.run(prepare_content(entry, selected, FakeClient()))
    entry.metadata["long_form"]["chunks"][-1]["notes"]["points"][0]["evidence"] = "Invented quote"
    with pytest.raises(LongFormError, match="does not occur"):
        prepared_content(entry, selected)


def test_oversized_notes_are_rejected_without_slicing_away_later_points():
    class OversizedClient(FakeClient):
        async def complete(self, **kwargs):
            self.requests.append(kwargs)
            return json.dumps({"points": [{"claim": "x" * 1000, "evidence": "actual evidence"}]})

    entry = item("actual evidence " * 40)
    client = OversizedClient()
    with pytest.raises(LongFormError, match="could not be verified"):
        asyncio.run(prepare_content(entry, profile(budget=1000), client))
    assert len(client.extraction_calls) == 2
    assert entry.metadata["long_form"]["status"] == "partial"


def test_profile_without_long_form_still_uses_existing_article_sampling():
    entry = item("head " * 1000 + "TAIL_FINDING")
    ordinary = BASE.get("tech-news")
    context = item_context(entry, ordinary, True)
    assert "head " in context
    assert "long_form" not in entry.metadata


def test_profile_rejects_unbounded_extraction_settings():
    with pytest.raises(ValueError):
        LongFormContent(max_chunks=10000)
    with pytest.raises(ValueError):
        LongFormContent(chunk_chars=0)


def test_podcast_without_complete_transcript_is_not_summarized_from_show_notes():
    entry = item("Show notes naming three topics but no actual interview text.")
    entry.source_type = SourceType.PODCAST
    entry.metadata["podcast"]["transcript_status"] = "missing"
    client = FakeClient()
    with pytest.raises(LongFormError, match="complete public transcript"):
        asyncio.run(prepare_content(entry, profile(), client))
    assert client.requests == []
    assert entry.metadata["long_form"]["status"] == "blocked"


def test_unrelated_podcast_metadata_does_not_break_normal_enrichment():
    selected = profile()
    selected.definition.content.long_form = None
    registry = ProfileRegistry({"tech-news": selected}, "tech-news")
    entry = item("The closing finding matters.")
    entry.metadata["podcast"] = "An unrelated metadata string"
    client = FakeClient()
    asyncio.run(ContentAnalyzer(client, registry)._analyze_item(entry))
    asyncio.run(ContentEnricher(client, registry, ["en"])._enrich_item(entry))
    assert entry.processing.artifacts["en"].sources == []
    assert client.extraction_calls == []


def test_corrupted_attempt_ledger_cannot_expand_model_call_budget():
    selected = profile()
    entry = item(transcript())
    client = FakeClient()
    asyncio.run(prepare_content(entry, selected, client))
    state = entry.metadata["long_form"]
    state["status"] = "partial"
    state["chunks"][-1] = None
    state["attempts"][-1] = -100
    with pytest.raises(LongFormError, match="Invalid long-form extraction cache"):
        asyncio.run(prepare_content(entry, selected, client))
    assert len(client.extraction_calls) == 3
