from __future__ import annotations

import json
from pathlib import Path

from src.config_ui.initialization import example_config, minimal_config
from src.configuration import validate_raw_config


def test_minimal_initialization_is_valid_and_returns_independent_drafts():
    first = minimal_config()
    second = minimal_config()

    first["sources"]["hackernews"]["enabled"] = False
    report = validate_raw_config(second, environ={"OPENAI_API_KEY": "set"}).report

    assert report.valid
    assert report.warnings == []
    assert second["sources"]["hackernews"]["enabled"] is True


def test_nearby_example_is_preferred_without_creating_active_config(
    tmp_path: Path,
):
    config_path = tmp_path / "config.json"
    example_path = tmp_path / "config.example.json"
    expected = {"version": "future-draft", "unknown": {"preserve": True}}
    example_path.write_text(json.dumps(expected), encoding="utf-8")

    draft = example_config(config_path)

    assert draft == expected
    assert not config_path.exists()


def test_invalid_examples_are_ignored(tmp_path: Path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.with_name("config.example.json").write_text(
        "{invalid",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert example_config(config_path) is None
    assert not config_path.exists()
