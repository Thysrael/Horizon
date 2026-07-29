from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.notion_agent.config import AgentConfig
from src.notion_agent.executor import (
    ExecutionError,
    LocalAgentExecutor,
    branch_name,
    is_forbidden_path,
    parse_allowed_paths,
    parse_output_file,
    validate_changed_files,
    validate_result,
)


def test_branch_name_contains_only_safe_segments() -> None:
    assert (
        branch_name(
            "3ab0efdb-ebab-814d-b212-df7a02767e95",
            "event:/ unsafe value",
        )
        == "codex/notion-3ab0efdbebab-eventuns"
    )


@pytest.mark.parametrize(
    "path",
    [
        "AGENTS.md",
        "src/AGENTS.md",
        ".codex/config.toml",
        ".github/workflows/release.yml",
        ".github/codex/prompts/task.md",
        ".env",
        ".env.production",
        "certificate.pem",
    ],
)
def test_control_plane_paths_are_forbidden(path: str) -> None:
    assert is_forbidden_path(path)


def test_allowed_paths_are_mechanically_enforced() -> None:
    patterns = parse_allowed_paths("src/**, tests/**")

    validate_changed_files(
        ["src/services/example.py", "tests/test_example.py"],
        patterns,
    )
    with pytest.raises(ExecutionError, match="outside"):
        validate_changed_files(["README.md"], patterns)


def test_parent_path_in_allowed_paths_is_rejected() -> None:
    with pytest.raises(ExecutionError, match="Unsafe"):
        parse_allowed_paths("../secrets/**")


def test_result_validation_requires_success_shape(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    value = {
        "status": "success",
        "summary": "Implemented.",
        "files_changed": ["src/example.py"],
        "verification": ["pytest"],
        "risks": [],
        "requires_human": False,
    }
    path.write_text(json.dumps(value), encoding="utf-8")

    assert validate_result(path) == value


def test_output_file_parser_ignores_malformed_lines(tmp_path: Path) -> None:
    path = tmp_path / "output"
    path.write_text("has_task=true\nbad\npage_id=abc=123\n", encoding="utf-8")

    assert parse_output_file(path) == {
        "has_task": "true",
        "page_id": "abc=123",
    }


def test_codex_command_pins_model_and_reasoning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    config = AgentConfig.from_env(
        {
            "HORIZON_REPO_ROOT": str(repo),
            "NOTION_DATA_SOURCE_ID": "67132048-6501-4156-be51-28a288d6b771",
            "NOTION_TOKEN": "test-token",
            "GITHUB_REPOSITORY": "example/horizon",
        }
    )
    executor = LocalAgentExecutor(config)
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Implement the task.", encoding="utf-8")
    captured: dict[str, object] = {}

    def capture(arguments: list[str], **kwargs: object) -> None:
        captured["arguments"] = arguments
        captured.update(kwargs)

    monkeypatch.setattr(executor, "_run_logged", capture)

    executor._run_codex(
        worktree=repo,
        prompt_file=prompt_file,
        run_dir=tmp_path,
    )

    arguments = captured["arguments"]
    assert isinstance(arguments, list)
    assert arguments[arguments.index("--model") + 1] == "gpt-5.6-sol"
    assert arguments[arguments.index("--config") + 1] == (
        'model_reasoning_effort="xhigh"'
    )
