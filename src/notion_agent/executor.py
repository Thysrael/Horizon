"""Execute queued Notion tasks with the locally authenticated Codex CLI."""

from __future__ import annotations

import fnmatch
import json
import logging
import os
import re
import shlex
import subprocess
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .config import AgentConfig
from .queue import EventJob, EventQueue

LOGGER = logging.getLogger(__name__)
REQUIRED_RESULT_FIELDS = {
    "status",
    "summary",
    "files_changed",
    "verification",
    "risks",
    "requires_human",
}


class ExecutionError(RuntimeError):
    """Raised when a local task cannot safely proceed."""


@dataclass(frozen=True)
class ExecutionOutcome:
    state: str
    message: str
    pr_url: str = ""


def _clean_identifier(value: str, *, limit: int = 24) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "", value)
    return cleaned[:limit].casefold() or "unknown"


def branch_name(page_id: str, event_id: str) -> str:
    return (
        f"codex/notion-{_clean_identifier(page_id, limit=12)}-"
        f"{_clean_identifier(event_id, limit=8)}"
    )


def parse_output_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def parse_allowed_paths(value: str) -> tuple[str, ...]:
    patterns: list[str] = []
    for item in re.split(r"[,\r\n]+", value):
        pattern = item.strip().replace("\\", "/")
        if not pattern:
            continue
        path = PurePosixPath(pattern)
        if path.is_absolute() or ".." in path.parts:
            raise ExecutionError(f"Unsafe Allowed Paths pattern: {pattern!r}")
        patterns.append(pattern)
    return tuple(patterns)


def is_forbidden_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    parts = PurePosixPath(normalized).parts
    name = parts[-1] if parts else ""
    protected_prefix = normalized.startswith(
        (
            ".agents/skills/",
            ".codex/",
            ".github/workflows/",
            ".github/codex/",
        )
    )
    return (
        name == "AGENTS.md"
        or normalized == ".env"
        or (normalized.startswith(".env.") and normalized != ".env.example")
        or protected_prefix
        or normalized.endswith((".pem", ".key", ".p12"))
    )


def path_is_allowed(path: str, patterns: Sequence[str]) -> bool:
    if not patterns:
        return True
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        if fnmatch.fnmatchcase(normalized, pattern):
            return True
        if pattern.endswith("/**") and normalized.startswith(pattern[:-3] + "/"):
            return True
    return False


def validate_changed_files(
    changed_files: Sequence[str],
    allowed_paths: Sequence[str],
    *,
    max_changed_files: int | None = None,
) -> None:
    if not changed_files:
        raise ExecutionError("Codex completed without producing a repository change")
    if max_changed_files is not None and len(changed_files) > max_changed_files:
        raise ExecutionError(
            f"Codex changed {len(changed_files)} files; the configured limit is "
            f"{max_changed_files}"
        )
    forbidden = sorted(path for path in changed_files if is_forbidden_path(path))
    if forbidden:
        raise ExecutionError(
            "Codex changed protected control-plane or secret paths: "
            + ", ".join(forbidden)
        )
    outside = sorted(
        path for path in changed_files if not path_is_allowed(path, allowed_paths)
    )
    if outside:
        raise ExecutionError(
            "Codex changed files outside the task Allowed Paths: " + ", ".join(outside)
        )


def validate_result(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ExecutionError("Codex did not produce a valid structured result") from exc
    if not isinstance(value, dict):
        raise ExecutionError("Codex structured result must be a JSON object")
    missing = REQUIRED_RESULT_FIELDS.difference(value)
    if missing:
        raise ExecutionError(
            "Codex structured result is missing: " + ", ".join(sorted(missing))
        )
    if value["status"] not in {"success", "blocked", "failed"}:
        raise ExecutionError("Codex structured result has an invalid status")
    for name in ("files_changed", "verification", "risks"):
        if not isinstance(value[name], list) or not all(
            isinstance(item, str) for item in value[name]
        ):
            raise ExecutionError(f"Codex structured result field {name!r} is invalid")
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        raise ExecutionError("Codex structured result summary is empty")
    if not isinstance(value["requires_human"], bool):
        raise ExecutionError("Codex structured result requires_human must be a boolean")
    return value


def _safe_message(value: str, *, limit: int = 1_500) -> str:
    sanitized = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]+", " ", value)
    sanitized = re.sub(
        r"(?i)(token|authorization|secret|api[_-]?key)\s*[:=]\s*\S+",
        r"\1=[redacted]",
        sanitized,
    )
    return sanitized.strip()[:limit]


class LocalAgentExecutor:
    """Orchestrate one claimed Notion page through a reviewable draft PR."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.notion_script = config.repo_root / "scripts" / "notion_coding.py"
        self.prompt_template = (
            config.repo_root / ".github" / "codex" / "prompts" / "notion-task.md"
        )
        self.result_schema = (
            config.repo_root
            / ".github"
            / "codex"
            / "schemas"
            / "notion-result.schema.json"
        )

    def _environment(self, *, job_id: str = "") -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "NOTION_TOKEN": self.config.notion_token,
                "NOTION_DATA_SOURCE_ID": self.config.notion_data_source_id,
                "GITHUB_REPOSITORY": self.config.repository,
                "GITHUB_DEFAULT_BRANCH": self.config.base_branch,
                "CODEX_VERIFICATION_COMMAND": shlex.join(
                    self.config.verification_command
                ),
                "CODEX_EXECUTION_SOURCE": "local webhook agent",
            }
        )
        if job_id:
            environment["CODEX_JOB_ID"] = job_id
        return environment

    def _run_capture(
        self,
        arguments: Sequence[str],
        *,
        cwd: Path,
        timeout: int = 120,
        environment: Mapping[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                list(arguments),
                cwd=cwd,
                env=dict(environment) if environment is not None else None,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ExecutionError(f"Command could not run: {arguments[0]}") from exc
        if check and result.returncode != 0:
            details = _safe_message(result.stderr or result.stdout)
            raise ExecutionError(
                f"Command failed ({arguments[0]}, exit {result.returncode}): "
                f"{details or 'no diagnostic output'}"
            )
        return result

    def _run_logged(
        self,
        arguments: Sequence[str],
        *,
        cwd: Path,
        log_path: Path,
        timeout: int,
        environment: Mapping[str, str] | None = None,
        input_text: str | None = None,
    ) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with log_path.open("w", encoding="utf-8") as log:
                result = subprocess.run(
                    list(arguments),
                    cwd=cwd,
                    env=dict(environment) if environment is not None else None,
                    input=input_text,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ExecutionError(f"Command could not complete: {arguments[0]}") from exc
        if result.returncode != 0:
            raise ExecutionError(
                f"Command failed ({arguments[0]}, exit {result.returncode}); "
                f"review {log_path}"
            )

    def _claim(
        self, job: EventJob, run_dir: Path
    ) -> tuple[dict[str, Any] | None, Path]:
        task_file = run_dir / "task.json"
        output_file = run_dir / "claim-output"
        command = [
            self.config.python_bin,
            str(self.notion_script),
            "claim",
            "--page-id",
            job.page_id,
            "--task-file",
            str(task_file),
            "--github-output",
            str(output_file),
            "--ignore-non-ready",
            "--resume-own-claim",
        ]
        self._run_capture(
            command,
            cwd=self.config.repo_root,
            timeout=180,
            environment=self._environment(job_id=f"local-{job.event_id}"),
        )
        outputs = parse_output_file(output_file)
        if outputs.get("has_task") != "true":
            return None, task_file
        try:
            task = json.loads(task_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise ExecutionError("Claimed Notion task JSON is invalid") from exc
        if not isinstance(task, dict):
            raise ExecutionError("Claimed Notion task must be a JSON object")
        return task, task_file

    def _render_prompt(self, task_file: Path, run_dir: Path, job_id: str) -> Path:
        prompt_file = run_dir / "prompt.md"
        self._run_capture(
            [
                self.config.python_bin,
                str(self.notion_script),
                "render",
                "--task-file",
                str(task_file),
                "--template",
                str(self.prompt_template),
                "--output",
                str(prompt_file),
            ],
            cwd=self.config.repo_root,
            environment=self._environment(job_id=job_id),
        )
        return prompt_file

    def _prepare_worktree(self, *, branch: str, worktree: Path) -> None:
        self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(self.config.repo_root),
                "fetch",
                "origin",
                self.config.base_branch,
            ],
            cwd=self.config.repo_root,
            timeout=300,
        )
        if worktree.exists():
            existing = self._run_capture(
                [
                    self.config.git_bin,
                    "-C",
                    str(worktree),
                    "rev-parse",
                    "--is-inside-work-tree",
                ],
                cwd=self.config.repo_root,
                check=False,
            )
            if existing.returncode == 0 and existing.stdout.strip() == "true":
                return
            raise ExecutionError(
                f"Existing recovery path is not a Git worktree: {worktree}"
            )

        worktree.parent.mkdir(parents=True, exist_ok=True)
        local_branch = self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(self.config.repo_root),
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/heads/{branch}",
            ],
            cwd=self.config.repo_root,
            check=False,
        )
        if local_branch.returncode == 0:
            self._run_capture(
                [
                    self.config.git_bin,
                    "-C",
                    str(self.config.repo_root),
                    "worktree",
                    "add",
                    str(worktree),
                    branch,
                ],
                cwd=self.config.repo_root,
                timeout=120,
            )
            return
        self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(self.config.repo_root),
                "worktree",
                "add",
                "-b",
                branch,
                str(worktree),
                f"origin/{self.config.base_branch}",
            ],
            cwd=self.config.repo_root,
            timeout=120,
        )

    def _run_codex(self, *, worktree: Path, prompt_file: Path, run_dir: Path) -> Path:
        result_file = run_dir / "codex-result.json"
        command = [
            self.config.codex_bin,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            "workspace-write",
            "--cd",
            str(worktree),
            "--output-schema",
            str(self.result_schema),
            "--output-last-message",
            str(result_file),
            "--json",
        ]
        if self.config.model:
            command.extend(["--model", self.config.model])
        command.append("-")
        self._run_logged(
            command,
            cwd=worktree,
            log_path=run_dir / "codex.jsonl",
            timeout=self.config.codex_timeout_seconds,
            environment=os.environ,
            input_text=prompt_file.read_text(encoding="utf-8"),
        )
        return result_file

    def _changed_files(self, worktree: Path) -> list[str]:
        committed = self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(worktree),
                "diff",
                "--name-only",
                "-z",
                f"origin/{self.config.base_branch}...HEAD",
            ],
            cwd=worktree,
        ).stdout.split("\0")
        working = self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(worktree),
                "diff",
                "--name-only",
                "-z",
                "HEAD",
            ],
            cwd=worktree,
        ).stdout.split("\0")
        untracked = self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(worktree),
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=worktree,
        ).stdout.split("\0")
        return sorted({path for path in committed + working + untracked if path})

    def _verify(self, worktree: Path, run_dir: Path) -> None:
        self._run_logged(
            self.config.verification_command,
            cwd=worktree,
            log_path=run_dir / "verification.log",
            timeout=self.config.verification_timeout_seconds,
            environment=os.environ,
        )

    def _prepare_pr(
        self,
        *,
        task_file: Path,
        result_file: Path,
        run_dir: Path,
        job_id: str,
    ) -> tuple[str, Path]:
        output_file = run_dir / "pr-output"
        body_file = run_dir / "pr-body.md"
        self._run_capture(
            [
                self.config.python_bin,
                str(self.notion_script),
                "pr-metadata",
                "--task-file",
                str(task_file),
                "--result-file",
                str(result_file),
                "--body-file",
                str(body_file),
                "--github-output",
                str(output_file),
                "--verification-exit-code",
                "0",
            ],
            cwd=self.config.repo_root,
            environment=self._environment(job_id=job_id),
        )
        title = parse_output_file(output_file).get("pr_title", "")
        if not title:
            raise ExecutionError("PR metadata did not contain a title")
        return title, body_file

    def _publish(
        self,
        *,
        worktree: Path,
        branch: str,
        title: str,
        body_file: Path,
        page_id: str,
    ) -> str:
        self._run_capture(
            [self.config.git_bin, "-C", str(worktree), "add", "--all"],
            cwd=worktree,
        )
        self._run_capture(
            [self.config.git_bin, "-C", str(worktree), "diff", "--cached", "--check"],
            cwd=worktree,
        )
        staged = self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(worktree),
                "diff",
                "--cached",
                "--quiet",
            ],
            cwd=worktree,
            check=False,
        )
        if staged.returncode != 0:
            self._run_capture(
                [
                    self.config.git_bin,
                    "-C",
                    str(worktree),
                    "commit",
                    "-m",
                    (
                        "feat: implement Notion task "
                        f"{_clean_identifier(page_id, limit=12)}"
                    ),
                ],
                cwd=worktree,
            )
        ahead = self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(worktree),
                "rev-list",
                "--count",
                f"origin/{self.config.base_branch}..HEAD",
            ],
            cwd=worktree,
        ).stdout.strip()
        if not ahead.isdigit() or int(ahead) < 1:
            raise ExecutionError("Publication branch has no commits above the base")
        self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(worktree),
                "push",
                "--set-upstream",
                "origin",
                branch,
            ],
            cwd=worktree,
            timeout=300,
        )
        existing = self._run_capture(
            [
                self.config.gh_bin,
                "pr",
                "list",
                "--repo",
                self.config.repository,
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "url",
                "--limit",
                "1",
            ],
            cwd=worktree,
            timeout=180,
        )
        try:
            existing_prs = json.loads(existing.stdout)
        except json.JSONDecodeError as exc:
            raise ExecutionError(
                "GitHub CLI returned invalid pull request metadata"
            ) from exc
        if (
            isinstance(existing_prs, list)
            and existing_prs
            and isinstance(existing_prs[0], dict)
        ):
            existing_url = str(existing_prs[0].get("url") or "")
            if existing_url.startswith("https://"):
                return existing_url
        result = self._run_capture(
            [
                self.config.gh_bin,
                "pr",
                "create",
                "--repo",
                self.config.repository,
                "--base",
                self.config.base_branch,
                "--head",
                branch,
                "--title",
                title,
                "--body-file",
                str(body_file),
                "--draft",
            ],
            cwd=worktree,
            timeout=180,
        )
        pr_url = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
        if not pr_url.startswith("https://"):
            raise ExecutionError("GitHub CLI did not return a pull request URL")
        return pr_url

    def _update_notion(
        self,
        *,
        page_id: str,
        status: str,
        result: str,
        pr_url: str = "",
        job_id: str,
    ) -> None:
        self._run_capture(
            [
                self.config.python_bin,
                str(self.notion_script),
                "update",
                "--page-id",
                page_id,
                "--status",
                status,
                "--pr-url",
                pr_url,
                "--result",
                _safe_message(result),
            ],
            cwd=self.config.repo_root,
            timeout=180,
            environment=self._environment(job_id=job_id),
        )

    def _remove_successful_worktree(self, worktree: Path) -> None:
        self._run_capture(
            [
                self.config.git_bin,
                "-C",
                str(self.config.repo_root),
                "worktree",
                "remove",
                str(worktree),
            ],
            cwd=self.config.repo_root,
        )

    def execute(self, job: EventJob) -> ExecutionOutcome:
        execution_id = f"local-{job.event_id}"
        run_dir = (
            self.config.runtime_dir / "runs" / _clean_identifier(execution_id, limit=64)
        )
        worktree = (
            self.config.runtime_dir
            / "worktrees"
            / _clean_identifier(execution_id, limit=64)
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        task_claimed = False
        pr_url = ""
        try:
            task, task_file = self._claim(job, run_dir)
            if task is None:
                return ExecutionOutcome(
                    "ignored",
                    "Page is no longer Ready for Codex",
                )
            task_claimed = True
            allowed_paths = parse_allowed_paths(str(task.get("allowed_paths") or ""))
            if self.config.require_allowed_paths and not allowed_paths:
                raise ExecutionError(
                    "Task must define narrow Allowed Paths before Codex can run"
                )
            risk = str(task.get("risk") or "").strip()
            allowed_risks = {value.casefold() for value in self.config.allowed_risks}
            if risk.casefold() not in allowed_risks:
                raise ExecutionError(
                    f"Task risk {risk or '(missing)'!r} is not allowed; "
                    f"configured risks: {', '.join(self.config.allowed_risks)}"
                )
            prompt_file = self._render_prompt(task_file, run_dir, execution_id)
            task_branch = branch_name(job.page_id, job.event_id)
            self._prepare_worktree(branch=task_branch, worktree=worktree)
            result_file = run_dir / "codex-result.json"
            try:
                result = validate_result(result_file)
            except ExecutionError:
                result_file = self._run_codex(
                    worktree=worktree,
                    prompt_file=prompt_file,
                    run_dir=run_dir,
                )
                result = validate_result(result_file)
            if result["status"] != "success" or result["requires_human"]:
                raise ExecutionError(
                    f"Codex returned {result['status']}: {result['summary']}"
                )

            changed_files = self._changed_files(worktree)
            validate_changed_files(
                changed_files,
                allowed_paths,
                max_changed_files=self.config.max_changed_files,
            )
            self._verify(worktree, run_dir)
            title, body_file = self._prepare_pr(
                task_file=task_file,
                result_file=result_file,
                run_dir=run_dir,
                job_id=execution_id,
            )
            pr_url = self._publish(
                worktree=worktree,
                branch=task_branch,
                title=title,
                body_file=body_file,
                page_id=job.page_id,
            )
            self._update_notion(
                page_id=job.page_id,
                status=os.environ.get("NOTION_REVIEW_STATUS", "Review"),
                result=f"Draft pull request created: {pr_url}",
                pr_url=pr_url,
                job_id=execution_id,
            )
            self._remove_successful_worktree(worktree)
            return ExecutionOutcome(
                "succeeded",
                f"Draft pull request created: {pr_url}",
                pr_url,
            )
        except Exception as exc:
            message = _safe_message(str(exc)) or type(exc).__name__
            LOGGER.exception("Notion event %s failed", job.event_id)
            if task_claimed:
                try:
                    self._update_notion(
                        page_id=job.page_id,
                        status=os.environ.get("NOTION_BLOCKED_STATUS", "Blocked"),
                        result=(
                            f"Local agent {execution_id} failed: {message}. "
                            f"Logs: {run_dir}"
                        ),
                        pr_url=pr_url,
                        job_id=execution_id,
                    )
                except Exception:
                    LOGGER.exception(
                        "Could not update failed Notion task %s", job.page_id
                    )
            if worktree.exists() and not self.config.keep_failed_worktrees:
                try:
                    self._run_capture(
                        [
                            self.config.git_bin,
                            "-C",
                            str(self.config.repo_root),
                            "worktree",
                            "remove",
                            "--force",
                            str(worktree),
                        ],
                        cwd=self.config.repo_root,
                    )
                except Exception:
                    LOGGER.exception("Could not remove failed worktree %s", worktree)
            return ExecutionOutcome("failed", message, pr_url)


class WorkerLoop:
    """Continuously drain one durable queue with a single Codex worker."""

    def __init__(
        self,
        queue: EventQueue,
        executor: LocalAgentExecutor,
        *,
        poll_seconds: float,
    ) -> None:
        self.queue = queue
        self.executor = executor
        self.poll_seconds = max(poll_seconds, 0.1)
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def process_once(self) -> bool:
        job = self.queue.claim_next()
        if job is None:
            return False
        outcome = self.executor.execute(job)
        self.queue.finish(job.event_id, outcome.state, outcome.message)
        return True

    def run(self) -> None:
        recovered = self.queue.recover_interrupted()
        if recovered:
            LOGGER.warning("Recovered %d interrupted Notion events", recovered)
        while not self._stop.is_set():
            try:
                processed = self.process_once()
            except Exception:
                LOGGER.exception("Unexpected local agent worker failure")
                processed = False
            if not processed:
                self._stop.wait(self.poll_seconds)
