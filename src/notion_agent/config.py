"""Configuration and secret storage for the local Notion agent."""

from __future__ import annotations

import os
import re
import shlex
import stat
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EVENTS = (
    "page.created",
    "page.properties_updated",
    "page.content_updated",
)
DEFAULT_CODEX_MODEL = "gpt-5.6-sol"
DEFAULT_CODEX_REASONING_EFFORT = "xhigh"
CODEX_REASONING_EFFORTS = frozenset(
    {"minimal", "low", "medium", "high", "xhigh"}
)


def _env(source: Mapping[str, str], name: str, default: str = "") -> str:
    return source.get(name, default).strip()


def _env_bool(source: Mapping[str, str], name: str, default: bool = False) -> bool:
    raw = _env(source, name)
    if not raw:
        return default
    normalized = raw.casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


def _env_int(
    source: Mapping[str, str],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int | None = None,
) -> int:
    raw = _env(source, name)
    value = int(raw) if raw else default
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value


def _normalize_id(value: str) -> str:
    return value.replace("-", "").casefold()


def _repository_slug(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""

    remote = result.stdout.strip()
    match = re.search(
        r"(?:github\.com[:/])(?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?$",
        remote,
    )
    return match.group("slug") if match else ""


@dataclass(frozen=True)
class AgentConfig:
    """Trusted local configuration for the webhook listener and executor."""

    repo_root: Path
    runtime_dir: Path
    host: str
    port: int
    notion_token: str
    notion_data_source_id: str
    notion_workspace_id: str
    notion_integration_id: str
    verification_token: str
    verification_token_file: Path
    webhook_bootstrap_secret: str
    allowed_event_types: tuple[str, ...]
    max_webhook_bytes: int
    queue_poll_seconds: float
    python_bin: str
    codex_bin: str
    git_bin: str
    gh_bin: str
    cloudflared_bin: str
    repository: str
    base_branch: str
    model: str
    reasoning_effort: str
    verification_command: tuple[str, ...]
    codex_timeout_seconds: int
    verification_timeout_seconds: int
    require_allowed_paths: bool
    allowed_risks: tuple[str, ...]
    max_changed_files: int
    keep_failed_worktrees: bool
    disable_worker: bool

    @classmethod
    def from_env(
        cls,
        source: Mapping[str, str] | None = None,
        *,
        require_notion_token: bool = True,
    ) -> AgentConfig:
        values = source if source is not None else os.environ
        repo_root = (
            Path(_env(values, "HORIZON_REPO_ROOT", str(Path.cwd())))
            .expanduser()
            .resolve()
        )
        runtime_dir = (
            Path(
                _env(
                    values,
                    "NOTION_AGENT_RUNTIME_DIR",
                    str(repo_root / ".codex-runtime" / "notion-agent"),
                )
            )
            .expanduser()
            .resolve()
        )
        notion_token = _env(values, "NOTION_TOKEN")
        if require_notion_token and not notion_token:
            raise ValueError("NOTION_TOKEN is required in the local agent environment")

        data_source_id = _env(values, "NOTION_DATA_SOURCE_ID")
        if not data_source_id:
            raise ValueError("NOTION_DATA_SOURCE_ID is required")
        if not repo_root.is_dir():
            raise ValueError(f"HORIZON_REPO_ROOT does not exist: {repo_root}")
        if not (repo_root / ".git").exists():
            raise ValueError(f"HORIZON_REPO_ROOT is not a Git repository: {repo_root}")

        raw_events = _env(
            values, "NOTION_WEBHOOK_EVENT_TYPES", ",".join(DEFAULT_EVENTS)
        )
        events = tuple(item.strip() for item in raw_events.split(",") if item.strip())
        if not events:
            raise ValueError("NOTION_WEBHOOK_EVENT_TYPES cannot be empty")
        raw_risks = _env(values, "NOTION_AGENT_ALLOWED_RISKS", "Low")
        allowed_risks = tuple(
            item.strip() for item in raw_risks.split(",") if item.strip()
        )
        if not allowed_risks:
            raise ValueError("NOTION_AGENT_ALLOWED_RISKS cannot be empty")

        command = _env(values, "CODEX_VERIFICATION_COMMAND", "uv run pytest")
        parsed_command = tuple(shlex.split(command, posix=os.name != "nt"))
        if not parsed_command:
            raise ValueError("CODEX_VERIFICATION_COMMAND cannot be empty")

        token_file = (
            Path(
                _env(
                    values,
                    "NOTION_WEBHOOK_TOKEN_FILE",
                    str(runtime_dir / "webhook-verification-token"),
                )
            )
            .expanduser()
            .resolve()
        )
        repository = _env(values, "GITHUB_REPOSITORY") or _repository_slug(repo_root)
        if not repository:
            raise ValueError(
                "GITHUB_REPOSITORY is required when origin is not a GitHub remote"
            )
        model = _env(values, "CODEX_MODEL") or DEFAULT_CODEX_MODEL
        reasoning_effort = (
            _env(values, "CODEX_REASONING_EFFORT")
            or DEFAULT_CODEX_REASONING_EFFORT
        ).casefold()
        if reasoning_effort not in CODEX_REASONING_EFFORTS:
            supported = ", ".join(sorted(CODEX_REASONING_EFFORTS))
            raise ValueError(
                f"CODEX_REASONING_EFFORT must be one of: {supported}"
            )

        return cls(
            repo_root=repo_root,
            runtime_dir=runtime_dir,
            host=_env(values, "NOTION_AGENT_HOST", "127.0.0.1"),
            port=_env_int(
                values,
                "NOTION_AGENT_PORT",
                4782,
                minimum=1,
                maximum=65_535,
            ),
            notion_token=notion_token,
            notion_data_source_id=data_source_id,
            notion_workspace_id=_env(values, "NOTION_WORKSPACE_ID"),
            notion_integration_id=_env(values, "NOTION_INTEGRATION_ID"),
            verification_token=_env(values, "NOTION_WEBHOOK_VERIFICATION_TOKEN"),
            verification_token_file=token_file,
            webhook_bootstrap_secret=_env(
                values,
                "NOTION_WEBHOOK_BOOTSTRAP_SECRET",
            ),
            allowed_event_types=events,
            max_webhook_bytes=_env_int(
                values,
                "NOTION_WEBHOOK_MAX_BYTES",
                1_048_576,
                minimum=1_024,
            ),
            queue_poll_seconds=float(
                _env(values, "NOTION_AGENT_QUEUE_POLL_SECONDS", "1.0")
            ),
            python_bin=_env(values, "PYTHON_BIN", "python"),
            codex_bin=_env(values, "CODEX_BIN", "codex"),
            git_bin=_env(values, "GIT_BIN", "git"),
            gh_bin=_env(values, "GH_BIN", "gh"),
            cloudflared_bin=_env(values, "CLOUDFLARED_BIN", "cloudflared"),
            repository=repository,
            base_branch=_env(values, "GITHUB_DEFAULT_BRANCH", "main"),
            model=model,
            reasoning_effort=reasoning_effort,
            verification_command=parsed_command,
            codex_timeout_seconds=_env_int(
                values,
                "CODEX_TIMEOUT_SECONDS",
                3_600,
                minimum=60,
            ),
            verification_timeout_seconds=_env_int(
                values,
                "CODEX_VERIFICATION_TIMEOUT_SECONDS",
                1_800,
                minimum=10,
            ),
            require_allowed_paths=_env_bool(
                values,
                "NOTION_AGENT_REQUIRE_ALLOWED_PATHS",
                True,
            ),
            allowed_risks=allowed_risks,
            max_changed_files=_env_int(
                values,
                "NOTION_AGENT_MAX_CHANGED_FILES",
                50,
                minimum=1,
            ),
            keep_failed_worktrees=_env_bool(
                values, "NOTION_AGENT_KEEP_FAILED_WORKTREES", True
            ),
            disable_worker=_env_bool(values, "NOTION_AGENT_DISABLE_WORKER", False),
        )

    def matches_data_source(self, candidate: str) -> bool:
        return _normalize_id(candidate) == _normalize_id(self.notion_data_source_id)


class VerificationTokenStore:
    """Load or securely capture the Notion webhook verification token."""

    def __init__(self, config: AgentConfig) -> None:
        self._configured = config.verification_token
        self.path = config.verification_token_file

    def get(self) -> str:
        if self._configured:
            return self._configured
        try:
            return self.path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""

    def capture(self, token: str) -> bool:
        normalized = token.strip()
        if not normalized:
            raise ValueError("Notion verification token cannot be empty")

        existing = self.get()
        if existing:
            return existing == normalized

        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                self.path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                stat.S_IRUSR | stat.S_IWUSR,
            )
        except FileExistsError:
            return self.get() == normalized

        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(normalized)
            handle.write("\n")
        return True
