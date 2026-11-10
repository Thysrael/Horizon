import asyncio
import json

import pytest

from src.models import AIConfig, AIProvider
from src.setup import ai_recommend


class _FakeClient:
    def __init__(self, response: str):
        self.response = response

    async def complete(self, **kwargs) -> str:
        return self.response


def _recommend(monkeypatch, response: str):
    monkeypatch.setattr(
        ai_recommend, "create_ai_client", lambda _config: _FakeClient(response)
    )
    config = AIConfig(provider=AIProvider.OLLAMA, model="llama3.1", api_key_env="")
    return asyncio.run(ai_recommend.get_ai_recommendations(config, "AI tools", []))


@pytest.mark.parametrize(
    "response",
    [
        "[]",
        '{"sources": "not a list"}',
        '{"sources": [null, 7]}',
    ],
)
def test_malformed_ai_recommendations_are_ignored(monkeypatch, response):
    assert _recommend(monkeypatch, response) == []


def test_valid_recommendations_survive_malformed_entries(monkeypatch):
    valid = {
        "type": "rss",
        "description": "AI research",
        "config": {"name": "Example", "url": "https://example.com/feed"},
    }
    response = json.dumps(
        {
            "sources": [
                valid,
                {"type": "unknown", "description": "bad", "config": {}},
                {"type": [], "description": "bad", "config": {}},
                {"type": "rss", "description": "bad", "config": []},
                {"type": "rss", "description": None, "config": {}},
            ]
        }
    )

    assert _recommend(monkeypatch, response) == [{**valid, "origin": "ai"}]
