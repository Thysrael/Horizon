"""Command-line entry point for the local Horizon Notion agent."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

from .config import AgentConfig, VerificationTokenStore
from .executor import LocalAgentExecutor, WorkerLoop
from .queue import EventQueue
from .webhook import create_app


def _load_environment(path: str) -> None:
    if path:
        env_path = Path(path).expanduser().resolve()
        if not env_path.is_file():
            raise ValueError(f"Environment file does not exist: {env_path}")
        load_dotenv(env_path, override=False)


def _command_status(arguments: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    output = (result.stdout + "\n" + result.stderr).strip()
    lowered = output.casefold()
    failed_text = (
        "failed to log in",
        "not logged",
        "not authenticated",
    )
    okay = result.returncode == 0 and not any(
        marker in lowered for marker in failed_text
    )
    last_line = output.splitlines()[-1] if output else ""
    return okay, last_line


def _preflight(config: AgentConfig) -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(
        (
            "Notion token",
            bool(config.notion_token),
            "configured" if config.notion_token else "missing",
        )
    )
    checks.append(
        (
            "Codex model",
            bool(config.model and config.reasoning_effort),
            f"{config.model} ({config.reasoning_effort})",
        )
    )
    checks.append(
        (
            "Webhook verification token",
            bool(VerificationTokenStore(config).get()),
            (
                "configured"
                if VerificationTokenStore(config).get()
                else "capture it during Notion subscription setup"
            ),
        )
    )
    token_store = VerificationTokenStore(config)
    checks.append(
        (
            "Webhook bootstrap protection",
            bool(token_store.get() or config.webhook_bootstrap_secret),
            (
                "verification token already captured"
                if token_store.get()
                else (
                    "configured"
                    if config.webhook_bootstrap_secret
                    else "set NOTION_WEBHOOK_BOOTSTRAP_SECRET before setup"
                )
            ),
        )
    )
    for label, command in (
        ("Codex OAuth", [config.codex_bin, "login", "status"]),
        ("Git", [config.git_bin, "--version"]),
        ("GitHub CLI", [config.gh_bin, "auth", "status"]),
        ("Cloudflare Tunnel", [config.cloudflared_bin, "--version"]),
    ):
        okay, detail = _command_status(command, config.repo_root)
        checks.append((label, okay, detail))

    for label, path in (
        ("Trusted prompt", config.repo_root / ".github/codex/prompts/notion-task.md"),
        (
            "Result schema",
            config.repo_root / ".github/codex/schemas/notion-result.schema.json",
        ),
        ("Notion bridge", config.repo_root / "scripts/notion_coding.py"),
    ):
        checks.append((label, path.is_file(), str(path)))

    width = max(len(label) for label, _, _ in checks)
    for label, okay, detail in checks:
        marker = "OK" if okay else "FAIL"
        print(f"{marker:4}  {label:<{width}}  {detail}")
    return 0 if all(okay for _, okay, _ in checks) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        default="",
        help="Load local secrets and settings from an ignored env file",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("NOTION_AGENT_LOG_LEVEL", "INFO"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("serve", help="Run the webhook listener and worker")
    subparsers.add_parser(
        "preflight", help="Check local OAuth, GitHub, and configuration"
    )
    subparsers.add_parser("status", help="Print durable queue counts as JSON")
    subparsers.add_parser(
        "process-once", help="Process at most one queued webhook event"
    )
    subparsers.add_parser(
        "verification-token",
        help="Print the locally captured Notion verification token",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        _load_environment(args.env_file)
        logging.basicConfig(
            level=getattr(logging, args.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        require_token = args.command not in {"verification-token"}
        config = AgentConfig.from_env(require_notion_token=require_token)
        queue = EventQueue(config.runtime_dir / "events.sqlite3")

        if args.command == "serve":
            uvicorn.run(
                create_app(config, queue=queue),
                host=config.host,
                port=config.port,
                log_level=args.log_level.casefold(),
            )
            return 0
        if args.command == "preflight":
            return _preflight(config)
        if args.command == "status":
            print(json.dumps(queue.counts(), sort_keys=True))
            return 0
        if args.command == "verification-token":
            token = VerificationTokenStore(config).get()
            if not token:
                print(
                    "No verification token has been captured yet.",
                    file=sys.stderr,
                )
                return 1
            print(token)
            return 0
        if args.command == "process-once":
            worker = WorkerLoop(
                queue,
                LocalAgentExecutor(config),
                poll_seconds=config.queue_poll_seconds,
            )
            return 0 if worker.process_once() else 2
        parser.error(f"Unknown command: {args.command}")
    except (ValueError, OSError) as exc:
        print(f"horizon-notion-agent: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
