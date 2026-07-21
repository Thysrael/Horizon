"""Regression tests for BYOK-safe Horizon console output."""

from __future__ import annotations

import asyncio
from io import StringIO
from types import SimpleNamespace

import pytest
from rich.console import Console

from src.orchestrator import HorizonOrchestrator


@pytest.mark.asyncio
async def test_run_redacts_runtime_byok_key_when_execute_raises():
    key = "sk-byok-provider-echo"
    output = StringIO()
    orchestrator = object.__new__(HorizonOrchestrator)
    orchestrator.runtime_api_key = key
    orchestrator.console = Console(file=output, force_terminal=False)
    orchestrator.email_manager = None
    orchestrator.webhook_notifier = None
    orchestrator.config = SimpleNamespace()

    async def fail_execute(_force_hours=None):
        raise RuntimeError(f"provider response: invalid bearer {key}")

    orchestrator.execute = fail_execute

    with pytest.raises(RuntimeError):
        await orchestrator.run()

    rendered = output.getvalue()
    assert key not in rendered
    assert "[REDACTED]" in rendered


@pytest.mark.asyncio
async def test_dedup_error_redacts_runtime_byok_key(monkeypatch):
    key = "sk-byok-dedup-echo"
    output = StringIO()
    orchestrator = object.__new__(HorizonOrchestrator)
    orchestrator.runtime_api_key = key
    orchestrator.console = Console(file=output, force_terminal=False)
    orchestrator.config = SimpleNamespace(ai=SimpleNamespace())

    class FailingClient:
        async def complete(self, **_kwargs):
            raise RuntimeError(f"authorization failure {key}")

    monkeypatch.setattr("src.orchestrator.create_ai_client", lambda *_args, **_kwargs: FailingClient())

    items = [
        SimpleNamespace(title="first", ai_tags=[], ai_summary=""),
        SimpleNamespace(title="second", ai_tags=[], ai_summary=""),
    ]
    assert await orchestrator.merge_topic_duplicates(items, log=True) == items
    rendered = output.getvalue()
    assert key not in rendered
    assert "[REDACTED]" in rendered
