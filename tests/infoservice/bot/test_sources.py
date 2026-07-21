import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.infoservice.bot.handlers import sources


def valid_payload(source_type: str) -> dict:
    return {
        "rss": {"name": "Python", "url": "https://example.com/feed.xml"},
        "telegram": {"channel": "python_news"},
        "hackernews": {},
        "github": {"type": "user_events", "username": "octocat"},
        "reddit": {"subreddit": "python"},
        "google_news": {"query": "Python"},
        "gdelt": {"query": "Python"},
        "ossinsight": {},
        "twitter": {"users": ["python"]},
        "openbb": {"name": "Tech", "symbols": ["MSFT"]},
    }[source_type]


@pytest.mark.parametrize("source_type", ["rss", "telegram", "hackernews", "github", "reddit", "google_news", "gdelt", "ossinsight", "twitter", "openbb"])
@pytest.mark.asyncio
async def test_stable_source_can_be_added(monkeypatch, source_type):
    report_id = uuid4()
    created = []

    class Repository:
        def __init__(self, session): pass
        async def add_source(self, owner_id, user_id, data):
            assert owner_id == report_id
            created.append(data)
            return SimpleNamespace(id=uuid4(), display_name=data.display_name, enabled=True)

    class State:
        data = {"source_draft": {"report_id": str(report_id), "source_type": source_type}}
        async def get_data(self): return self.data
        async def clear(self): pass

    class Message:
        text = json.dumps(valid_payload(source_type))
        answers = []
        async def answer(self, text, **_kwargs): self.answers.append(text)

    monkeypatch.setattr(sources, "ReportRepository", Repository)
    message = Message()
    await sources.receive_source_config(message, State(), object(), SimpleNamespace(id=uuid4()), SimpleNamespace(enable_twitter=True, enable_openbb=True))

    assert created[0].source_type == source_type


def test_disabled_optional_source_is_not_offered():
    labels = sources.available_source_labels(SimpleNamespace(enable_twitter=False, enable_openbb=False))
    assert "Twitter / X" not in labels
    assert "OpenBB" not in labels
    assert "RSS-лента" in labels


def test_enabled_optional_sources_are_offered():
    labels = sources.available_source_labels(SimpleNamespace(enable_twitter=True, enable_openbb=True))
    assert "Twitter / X" in labels
    assert "OpenBB" in labels
