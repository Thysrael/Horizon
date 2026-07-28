#!/usr/bin/env python3
"""Bridge a Notion task database to the Horizon Codex GitHub workflow.

The network-facing commands intentionally use only the Python standard library
so the intake and final status update jobs do not need project dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NOTION_API_BASE = "https://api.notion.com/v1"
DEFAULT_NOTION_VERSION = "2026-03-11"
DEFAULT_MAX_TASK_CHARS = 30_000
MAX_NOTION_RICH_TEXT_CHARS = 1_900


class NotionAPIError(RuntimeError):
    """Raised when the Notion API rejects or cannot complete a request."""


class NotionClient:
    """Small Notion REST client with bounded retries for transient failures."""

    def __init__(
        self,
        token: str,
        *,
        notion_version: str = DEFAULT_NOTION_VERSION,
        timeout: float = 30.0,
        max_attempts: int = 3,
    ) -> None:
        if not token:
            raise ValueError("NOTION_TOKEN is required")
        self._token = token
        self._notion_version = notion_version
        self._timeout = timeout
        self._max_attempts = max_attempts

    def _request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        request = urllib.request.Request(
            f"{NOTION_API_BASE}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Notion-Version": self._notion_version,
                "Content-Type": "application/json",
                "User-Agent": "horizon-notion-codex/1",
            },
        )

        for attempt in range(1, self._max_attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    raw = response.read()
                    return json.loads(raw.decode("utf-8")) if raw else {}
            except urllib.error.HTTPError as exc:
                response_body = exc.read().decode("utf-8", errors="replace")
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if retryable and attempt < self._max_attempts:
                    retry_after = exc.headers.get("Retry-After")
                    try:
                        delay = (
                            float(retry_after)
                            if retry_after
                            else 2 ** (attempt - 1)
                        )
                    except ValueError:
                        delay = 2 ** (attempt - 1)
                    time.sleep(min(delay, 10.0))
                    continue
                raise NotionAPIError(
                    f"Notion API {method} {path} failed with HTTP {exc.code}: "
                    f"{response_body[:500]}"
                ) from exc
            except urllib.error.URLError as exc:
                if attempt < self._max_attempts:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise NotionAPIError(
                    f"Notion API {method} {path} could not be reached: {exc.reason}"
                ) from exc

        raise NotionAPIError(f"Notion API {method} {path} exhausted retries")

    def query_ready_page(
        self,
        data_source_id: str,
        *,
        status_property: str,
        ready_status: str,
    ) -> dict[str, Any] | None:
        if not data_source_id:
            raise ValueError("NOTION_DATA_SOURCE_ID is required")
        encoded_id = urllib.parse.quote(data_source_id, safe="")
        payload = {
            "page_size": 1,
            "filter": {
                "property": status_property,
                "status": {"equals": ready_status},
            },
            "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
        }
        response = self._request(
            "POST", f"/data_sources/{encoded_id}/query", payload
        )
        results = response.get("results", [])
        return results[0] if results else None

    def retrieve_page(self, page_id: str) -> dict[str, Any]:
        encoded_id = urllib.parse.quote(page_id, safe="")
        return self._request("GET", f"/pages/{encoded_id}")

    def update_page(
        self, page_id: str, properties: Mapping[str, Any]
    ) -> dict[str, Any]:
        encoded_id = urllib.parse.quote(page_id, safe="")
        return self._request(
            "PATCH", f"/pages/{encoded_id}", {"properties": dict(properties)}
        )

    def retrieve_block_children(self, block_id: str) -> list[dict[str, Any]]:
        encoded_id = urllib.parse.quote(block_id, safe="")
        cursor: str | None = None
        blocks: list[dict[str, Any]] = []
        while True:
            query: dict[str, str | int] = {"page_size": 100}
            if cursor:
                query["start_cursor"] = cursor
            path = (
                f"/blocks/{encoded_id}/children?"
                f"{urllib.parse.urlencode(query)}"
            )
            response = self._request("GET", path)
            blocks.extend(response.get("results", []))
            if not response.get("has_more"):
                return blocks
            cursor = response.get("next_cursor")
            if not cursor:
                return blocks


def _plain_text(rich_text: Iterable[Mapping[str, Any]]) -> str:
    return "".join(str(item.get("plain_text", "")) for item in rich_text)


def _property(page: Mapping[str, Any], name: str) -> Mapping[str, Any] | None:
    properties = page.get("properties", {})
    value = properties.get(name)
    return value if isinstance(value, Mapping) else None


def page_title(page: Mapping[str, Any], property_name: str) -> str:
    prop = _property(page, property_name)
    if not prop:
        raise ValueError(f"Notion title property {property_name!r} does not exist")
    if prop.get("type") != "title":
        raise ValueError(
            f"Notion property {property_name!r} must be a title property"
        )
    title = _plain_text(prop.get("title", [])).strip()
    return title or "Untitled Notion task"


def page_status(page: Mapping[str, Any], property_name: str) -> str | None:
    prop = _property(page, property_name)
    if not prop:
        raise ValueError(f"Notion status property {property_name!r} does not exist")
    prop_type = prop.get("type")
    if prop_type not in {"status", "select"}:
        raise ValueError(
            f"Notion property {property_name!r} must be a status or select property"
        )
    selected = prop.get(prop_type)
    return selected.get("name") if isinstance(selected, Mapping) else None


def optional_text_property(page: Mapping[str, Any], property_name: str) -> str:
    if not property_name:
        return ""
    prop = _property(page, property_name)
    if not prop:
        return ""
    prop_type = prop.get("type")
    if prop_type in {"rich_text", "title"}:
        return _plain_text(prop.get(prop_type, [])).strip()
    if prop_type in {"select", "status"}:
        selected = prop.get(prop_type)
        return (
            str(selected.get("name", "")).strip()
            if isinstance(selected, Mapping)
            else ""
        )
    if prop_type == "multi_select":
        return ", ".join(
            str(item.get("name", "")).strip()
            for item in prop.get("multi_select", [])
            if item.get("name")
        )
    if prop_type == "url":
        return str(prop.get("url") or "").strip()
    return ""


def _block_text(block: Mapping[str, Any]) -> str:
    block_type = str(block.get("type", ""))
    payload = block.get(block_type, {})
    if not isinstance(payload, Mapping):
        return ""

    text = _plain_text(payload.get("rich_text", [])).strip()
    if block_type == "heading_1":
        return f"# {text}"
    if block_type == "heading_2":
        return f"## {text}"
    if block_type == "heading_3":
        return f"### {text}"
    if block_type == "bulleted_list_item":
        return f"- {text}"
    if block_type == "numbered_list_item":
        return f"1. {text}"
    if block_type == "to_do":
        marker = "x" if payload.get("checked") else " "
        return f"- [{marker}] {text}"
    if block_type == "quote":
        return f"> {text}"
    if block_type == "callout":
        return f"> {text}"
    if block_type == "toggle":
        return f"- {text}"
    if block_type == "code":
        language = str(payload.get("language") or "")
        return f"```{language}\n{text}\n```"
    if block_type == "divider":
        return "---"
    if block_type in {"child_page", "child_database"}:
        title = str(payload.get("title") or "").strip()
        return f"## {title}" if title else ""
    if block_type == "table_row":
        cells = payload.get("cells", [])
        return "| " + " | ".join(_plain_text(cell) for cell in cells) + " |"
    if block_type in {"bookmark", "embed", "link_preview"}:
        url = str(payload.get("url") or "").strip()
        return f"[{block_type}]({url})" if url else ""
    if block_type in {"image", "video", "audio", "file", "pdf"}:
        file_value = payload.get(payload.get("type", ""), {})
        url = file_value.get("url") if isinstance(file_value, Mapping) else ""
        caption = _plain_text(payload.get("caption", [])).strip() or block_type
        return f"[{caption}]({url})" if url else f"[{caption}]"
    return text


def collect_page_content(
    client: NotionClient,
    page_id: str,
    *,
    max_depth: int = 4,
    max_chars: int = DEFAULT_MAX_TASK_CHARS,
) -> str:
    lines: list[str] = []
    current_chars = 0

    def visit(parent_id: str, depth: int) -> bool:
        nonlocal current_chars
        for block in client.retrieve_block_children(parent_id):
            line = _block_text(block)
            if line:
                rendered = f"{'  ' * depth}{line}"
                if current_chars + len(rendered) + 1 > max_chars:
                    lines.append("[Notion content truncated by workflow limit]")
                    return False
                lines.append(rendered)
                current_chars += len(rendered) + 1

            if block.get("has_children"):
                if depth >= max_depth:
                    omitted = f"{'  ' * (depth + 1)}[Nested content omitted]"
                    lines.append(omitted)
                    current_chars += len(omitted) + 1
                    continue
                if not visit(str(block["id"]), depth + 1):
                    return False
        return True

    visit(page_id, 0)
    content = "\n".join(lines).strip()
    return content or "(The Notion page has no body blocks.)"


def _property_update(
    page: Mapping[str, Any],
    property_name: str,
    value: str,
) -> dict[str, Any] | None:
    if not property_name:
        return None
    prop = _property(page, property_name)
    if not prop:
        return None
    prop_type = prop.get("type")
    if prop_type == "status":
        return {"status": {"name": value}}
    if prop_type == "select":
        return {"select": {"name": value}}
    if prop_type == "url":
        return {"url": value or None}
    if prop_type == "rich_text":
        content = value[:MAX_NOTION_RICH_TEXT_CHARS]
        return {
            "rich_text": (
                [{"type": "text", "text": {"content": content}}] if content else []
            )
        }
    return None


def build_page_updates(
    page: Mapping[str, Any],
    *,
    status_property: str,
    status: str,
    run_id_property: str = "",
    run_id: str = "",
    pr_url_property: str = "",
    pr_url: str = "",
    result_property: str = "",
    result: str = "",
) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    status_update = _property_update(page, status_property, status)
    if not status_update:
        raise ValueError(
            f"Notion status property {status_property!r} must exist and be "
            "a status or select property"
        )
    updates[status_property] = status_update

    optional_values = (
        (run_id_property, run_id),
        (pr_url_property, pr_url),
        (result_property, result),
    )
    for property_name, value in optional_values:
        if not property_name or not value:
            continue
        update = _property_update(page, property_name, value)
        if update:
            updates[property_name] = update
    return updates


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _append_github_output(path: str, name: str, value: str) -> None:
    if "\n" in value or "\r" in value:
        raise ValueError(f"GitHub output {name!r} must be a single line")
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def _workflow_job_id() -> str:
    run_id = _env("GITHUB_RUN_ID", "local")
    attempt = _env("GITHUB_RUN_ATTEMPT", "1")
    return f"github-{run_id}-{attempt}"


def claim_task(args: argparse.Namespace) -> int:
    client = NotionClient(
        _env("NOTION_TOKEN"),
        notion_version=_env("NOTION_API_VERSION", DEFAULT_NOTION_VERSION),
    )
    status_property = _env("NOTION_STATUS_PROPERTY", "Status")
    ready_status = _env("NOTION_READY_STATUS", "Ready for Codex")
    page_id = args.page_id.strip()

    if page_id:
        page = client.retrieve_page(page_id)
        actual_status = page_status(page, status_property)
        if actual_status != ready_status:
            raise ValueError(
                f"Notion page status is {actual_status!r}; expected {ready_status!r}"
            )
    else:
        page = client.query_ready_page(
            _env("NOTION_DATA_SOURCE_ID"),
            status_property=status_property,
            ready_status=ready_status,
        )

    if not page:
        _append_github_output(args.github_output, "has_task", "false")
        return 0

    page_id = str(page["id"])
    max_chars = int(
        _env("NOTION_MAX_TASK_CHARS", str(DEFAULT_MAX_TASK_CHARS))
    )
    if max_chars < 1_000:
        raise ValueError("NOTION_MAX_TASK_CHARS must be at least 1000")
    task = {
        "schema_version": 1,
        "job_id": _workflow_job_id(),
        "page_id": page_id,
        "page_url": str(page.get("url") or ""),
        "title": page_title(
            page, _env("NOTION_TITLE_PROPERTY", "Task")
        ),
        "body": collect_page_content(client, page_id, max_chars=max_chars),
        "risk": optional_text_property(
            page, _env("NOTION_RISK_PROPERTY", "Risk")
        ),
        "allowed_paths": optional_text_property(
            page, _env("NOTION_ALLOWED_PATHS_PROPERTY", "Allowed Paths")
        ),
        "requested_verification": optional_text_property(
            page, _env("NOTION_VERIFICATION_PROPERTY", "Verification")
        ),
        "repository": _env("GITHUB_REPOSITORY"),
        "base_ref": _env("GITHUB_DEFAULT_BRANCH", "main"),
        "claimed_at": datetime.now(UTC).isoformat(),
    }
    task_path = Path(args.task_file)
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        json.dumps(task, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    working_status = _env("NOTION_WORKING_STATUS", "Coding")
    updates = build_page_updates(
        page,
        status_property=status_property,
        status=working_status,
        run_id_property=_env("NOTION_RUN_ID_PROPERTY", "Agent Run ID"),
        run_id=task["job_id"],
        result_property=_env("NOTION_RESULT_PROPERTY", "Agent Result"),
        result=f"Claimed by GitHub Actions run {task['job_id']}",
    )
    client.update_page(page_id, updates)

    _append_github_output(args.github_output, "has_task", "true")
    _append_github_output(args.github_output, "page_id", page_id)
    _append_github_output(args.github_output, "job_id", task["job_id"])
    return 0


def render_prompt_text(
    template: str,
    task: Mapping[str, Any],
    *,
    verification_command: str,
) -> str:
    replacements = {
        "{{TASK_JSON}}": json.dumps(task, ensure_ascii=False, indent=2),
        "{{VERIFICATION_COMMAND}}": verification_command,
        "{{REPOSITORY}}": str(task.get("repository") or ""),
        "{{BASE_REF}}": str(task.get("base_ref") or "main"),
    }
    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    remaining = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", rendered)))
    if remaining:
        raise ValueError(f"Unresolved prompt placeholders: {', '.join(remaining)}")
    return rendered


def render_prompt(args: argparse.Namespace) -> int:
    task = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8")
    verification_command = _env(
        "CODEX_VERIFICATION_COMMAND", "uv run pytest"
    )
    rendered = render_prompt_text(
        template, task, verification_command=verification_command
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return 0


def _single_line(value: str, *, max_length: int = 110) -> str:
    sanitized = re.sub(r"[\x00-\x1f\x7f]+", " ", value)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized[:max_length].rstrip()


def _markdown_list(values: Sequence[Any], fallback: str) -> str:
    rendered = [f"- {value!s}" for value in values if str(value).strip()]
    return "\n".join(rendered) if rendered else f"- {fallback}"


def build_pr_metadata(
    task: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    verification_command: str,
    verification_exit_code: str,
) -> tuple[str, str]:
    task_title = _single_line(str(task.get("title") or "Notion task"))
    pr_title = _single_line(f"Codex: {task_title}", max_length=120)
    source_url = str(task.get("page_url") or "")
    summary = str(result.get("summary") or "Codex completed the requested change.")
    status = str(result.get("status") or "unknown")
    changed_files = result.get("files_changed")
    tests = result.get("verification")
    risks = result.get("risks")

    if not isinstance(changed_files, list):
        changed_files = []
    if not isinstance(tests, list):
        tests = []
    if not isinstance(risks, list):
        risks = []

    body = f"""## Summary

{summary}

## Source

- Notion task: {source_url or "(URL unavailable)"}
- Workflow job: `{task.get("job_id", "unknown")}`
- Agent status: `{status}`
- Declared risk: {task.get("risk") or "not specified"}

## Changed Files

{_markdown_list(changed_files, "See the pull request diff.")}

## Verification

- Deterministic command: `{verification_command}`
- Deterministic exit code: `{verification_exit_code}`

{_markdown_list(tests, "No additional agent-reported checks.")}

## Risks and Follow-up

{_markdown_list(risks, "No additional risks reported.")}

---

This is an automatically generated **draft** pull request. Review the Notion
requirements, code diff, and required checks before marking it ready.
"""
    return pr_title, body


def pr_metadata(args: argparse.Namespace) -> int:
    task = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
    result_path = Path(args.result_file)
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        result = {
            "status": "unknown",
            "summary": "Codex produced changes but no valid structured result.",
            "files_changed": [],
            "verification": [],
            "risks": ["Structured Codex result was unavailable."],
        }
    if not isinstance(result, Mapping):
        result = {
            "status": "unknown",
            "summary": "Codex returned a non-object structured result.",
            "files_changed": [],
            "verification": [],
            "risks": ["Structured Codex result had the wrong top-level type."],
        }

    verification_command = _env(
        "CODEX_VERIFICATION_COMMAND", "uv run pytest"
    )
    title, body = build_pr_metadata(
        task,
        result,
        verification_command=verification_command,
        verification_exit_code=args.verification_exit_code,
    )
    body_path = Path(args.body_file)
    body_path.parent.mkdir(parents=True, exist_ok=True)
    body_path.write_text(body, encoding="utf-8")
    _append_github_output(args.github_output, "pr_title", title)
    return 0


def update_task(args: argparse.Namespace) -> int:
    client = NotionClient(
        _env("NOTION_TOKEN"),
        notion_version=_env("NOTION_API_VERSION", DEFAULT_NOTION_VERSION),
    )
    page = client.retrieve_page(args.page_id)
    updates = build_page_updates(
        page,
        status_property=_env("NOTION_STATUS_PROPERTY", "Status"),
        status=args.status,
        pr_url_property=_env("NOTION_PR_URL_PROPERTY", "PR URL"),
        pr_url=args.pr_url,
        result_property=_env("NOTION_RESULT_PROPERTY", "Agent Result"),
        result=args.result,
    )
    client.update_page(args.page_id, updates)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    claim = subparsers.add_parser("claim", help="Claim the oldest ready task")
    claim.add_argument("--page-id", default="")
    claim.add_argument("--task-file", required=True)
    claim.add_argument("--github-output", required=True)
    claim.set_defaults(func=claim_task)

    render = subparsers.add_parser("render", help="Render the trusted Codex prompt")
    render.add_argument("--task-file", required=True)
    render.add_argument("--template", required=True)
    render.add_argument("--output", required=True)
    render.set_defaults(func=render_prompt)

    metadata = subparsers.add_parser(
        "pr-metadata", help="Build a safe draft PR title and body"
    )
    metadata.add_argument("--task-file", required=True)
    metadata.add_argument("--result-file", required=True)
    metadata.add_argument("--body-file", required=True)
    metadata.add_argument("--github-output", required=True)
    metadata.add_argument("--verification-exit-code", required=True)
    metadata.set_defaults(func=pr_metadata)

    update = subparsers.add_parser("update", help="Update the Notion task status")
    update.add_argument("--page-id", required=True)
    update.add_argument("--status", required=True)
    update.add_argument("--pr-url", default="")
    update.add_argument("--result", required=True)
    update.set_defaults(func=update_task)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (NotionAPIError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"notion-coding: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
