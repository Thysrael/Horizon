"""Offline initialization drafts for a missing configuration file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def minimal_config() -> dict[str, Any]:
    """Return a small valid raw configuration without resolving credentials."""

    return {
        "version": "1.0",
        "ai": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key_env": "OPENAI_API_KEY",
        },
        "sources": {"hackernews": {"enabled": True}},
        "filtering": {
            "ai_score_threshold": 7.0,
            "time_window_hours": 24,
            "category_groups": {},
            "default_group": "other",
        },
    }


def example_config(config_path: Path) -> dict[str, Any] | None:
    """Load a nearby example as a draft, never as an implicit write."""

    candidates = (
        config_path.with_name("config.example.json"),
        Path.cwd() / "data" / "config.example.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            try:
                value = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if isinstance(value, dict):
                return value
    return None
