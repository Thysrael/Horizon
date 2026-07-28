from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.notion_agent.executor import (
    ExecutionError,
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
