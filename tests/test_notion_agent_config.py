from __future__ import annotations

from pathlib import Path

import pytest

from src.notion_agent.config import AgentConfig


def _environment(repo: Path) -> dict[str, str]:
    return {
        "HORIZON_REPO_ROOT": str(repo),
        "NOTION_DATA_SOURCE_ID": "67132048-6501-4156-be51-28a288d6b771",
        "NOTION_TOKEN": "test-token",
        "GITHUB_REPOSITORY": "example/horizon",
    }


def test_codex_model_and_reasoning_are_pinned_by_default(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    config = AgentConfig.from_env(_environment(repo))

    assert config.model == "gpt-5.6-sol"
    assert config.reasoning_effort == "xhigh"


def test_blank_codex_settings_fall_back_to_pinned_values(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    environment = _environment(repo)
    environment["CODEX_MODEL"] = ""
    environment["CODEX_REASONING_EFFORT"] = ""

    config = AgentConfig.from_env(environment)

    assert config.model == "gpt-5.6-sol"
    assert config.reasoning_effort == "xhigh"


def test_codex_reasoning_effort_is_validated(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    environment = _environment(repo)
    environment["CODEX_REASONING_EFFORT"] = "turbo"

    with pytest.raises(ValueError, match="CODEX_REASONING_EFFORT"):
        AgentConfig.from_env(environment)
