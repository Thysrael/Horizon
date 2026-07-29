"""Reliable daily runner for Horizon's local Codex provider."""

from __future__ import annotations

import argparse
import asyncio
import errno
import json
import math
import os
import re
import shutil
import subprocess
from datetime import datetime, time, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ._file_utils import _atomic_write_text
from .ai.client import CodexCLIClient
from .models import AIProvider
from .orchestrator import HorizonOrchestrator
from .storage.manager import StorageManager

MAX_CATCHUP_HOURS = 24 * 7
CATCHUP_BUFFER_HOURS = 2
_DAILY_AT_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class LockUnavailable(RuntimeError):
    """Raised when another daily runner owns the instance lock."""


class SingleInstanceLock:
    """A small cross-platform, non-blocking advisory file lock."""

    def __init__(self, path: Path):
        self.path = path
        self._file = None

    def __enter__(self) -> "SingleInstanceLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a+", encoding="utf-8")
        try:
            if os.name == "nt":
                import msvcrt

                self._file.seek(0, os.SEEK_END)
                if self._file.tell() == 0:
                    self._file.write("\0")
                    self._file.flush()
                self._file.seek(0)
                msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(
                    self._file.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
        except OSError as exc:
            self._file.close()
            self._file = None
            if isinstance(exc, BlockingIOError) or exc.errno in {
                errno.EACCES,
                errno.EAGAIN,
            }:
                raise LockUnavailable from exc
            raise
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._file is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                self._file.seek(0)
                msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        finally:
            self._file.close()
            self._file = None


def _runner_paths(config_path: Path) -> dict[str, Path]:
    data_dir = config_path.expanduser().resolve().parent
    return {
        "state": data_dir / "codex-daily-state.json",
        "lock": data_dir / "codex-daily.lock",
        "reports": data_dir / "run-reports",
        "summaries": data_dir / "summaries",
    }


def _now(run_timezone: tzinfo) -> datetime:
    return datetime.now(run_timezone)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2)
    _atomic_write_text(path, f"{content}\n")


def resolve_timezone(name: str | None) -> tzinfo:
    """Resolve an IANA timezone, or use the host's current local timezone."""
    if name is None:
        local_timezone = datetime.now().astimezone().tzinfo
        if local_timezone is None:
            raise ValueError("Could not determine the system timezone")
        return local_timezone
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {name}") from exc


def parse_daily_at(value: str) -> time:
    """Parse a strict 24-hour ``HH:MM`` value."""
    if not _DAILY_AT_PATTERN.fullmatch(value):
        raise ValueError("--daily-at must use 24-hour HH:MM format")
    return time.fromisoformat(value)


def _parse_timestamp(value: Any, default_timezone: tzinfo) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=default_timezone)
    return moment


def is_due(now: datetime, daily_at: time) -> bool:
    """Return whether today's configured start time has arrived."""
    return now.timetz().replace(tzinfo=None) >= daily_at


def should_skip_today(
    state: dict[str, Any],
    now: datetime,
    run_timezone: tzinfo,
) -> bool:
    """Return whether a successful run already exists for the local date."""
    last_success = _parse_timestamp(state.get("last_success_at"), run_timezone)
    if last_success is None:
        return False
    return (
        last_success.astimezone(run_timezone).date()
        == now.astimezone(run_timezone).date()
    )


def calculate_fetch_hours(
    configured_hours: int,
    now: datetime,
    last_success: datetime | None,
) -> int:
    """Cover downtime since the last success, with overlap and a seven-day cap."""
    if last_success is None:
        return min(configured_hours, MAX_CATCHUP_HOURS)
    elapsed = max((now - last_success).total_seconds(), 0)
    catchup = math.ceil(elapsed / 3600) + CATCHUP_BUFFER_HOURS
    return min(max(configured_hours, catchup), MAX_CATCHUP_HOURS)


def _codex_is_logged_in(stdout: str, stderr: str) -> bool:
    return "logged in" in f"{stdout}\n{stderr}".lower()


def _load_and_validate_codex_config(config_path: Path):
    storage = StorageManager(
        data_dir=str(config_path.parent),
        config_path=config_path,
    )
    config = storage.load_config()
    if config.ai.provider != AIProvider.CODEX:
        raise RuntimeError(
            f"Expected ai.provider=codex, got {config.ai.provider.value}"
        )
    if config.ai.provider_chain:
        raise RuntimeError("horizon-codex-daily does not support provider_chain")
    if config.ai.api_key_env:
        raise RuntimeError("The Codex provider must not require an API key")

    binary = os.getenv("HORIZON_CODEX_BIN") or shutil.which("codex")
    if not binary:
        raise RuntimeError("Codex CLI is not available on PATH")
    login = subprocess.run(
        [binary, "login", "status"],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    if login.returncode != 0 or not _codex_is_logged_in(
        login.stdout,
        login.stderr,
    ):
        detail = (login.stderr or login.stdout).strip()
        raise RuntimeError(f"Codex is not logged in: {detail}")

    CodexCLIClient(config.ai)
    return config


async def _run_pipeline(config_path: Path, fetch_hours: int) -> dict[str, Any]:
    storage = StorageManager(
        data_dir=str(config_path.parent),
        config_path=config_path,
    )
    config = storage.load_config()
    orchestrator = HorizonOrchestrator(config, storage)
    await orchestrator.run(force_hours=fetch_hours)
    if orchestrator.last_fetch_report is None:
        return {}
    return orchestrator.last_fetch_report.to_dict()


def _summary_snapshot(directory: Path) -> dict[Path, tuple[int, int]]:
    if not directory.exists():
        return {}
    return {
        path.resolve(): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in directory.glob("horizon-*.md")
        if path.is_file()
    }


def _changed_summaries(
    before: dict[Path, tuple[int, int]],
    after: dict[Path, tuple[int, int]],
) -> list[str]:
    return sorted(
        str(path)
        for path, signature in after.items()
        if before.get(path) != signature
    )


def run_once(
    *,
    config_path: Path,
    run_timezone: tzinfo,
    daily_at: time,
    force: bool = False,
    now: datetime | None = None,
) -> int:
    """Execute one guarded Codex daily run."""
    paths = _runner_paths(config_path)
    current = now or _now(run_timezone)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = current.astimezone(run_timezone)

    try:
        lock = SingleInstanceLock(paths["lock"])
        lock.__enter__()
    except LockUnavailable:
        print("SKIP: another Horizon Codex daily run is active")
        return 0

    try:
        state = _load_json(paths["state"])
        if not force and not is_due(current, daily_at):
            print(
                f"SKIP: daily start time {daily_at.strftime('%H:%M')} "
                "has not arrived"
            )
            return 0
        if not force and should_skip_today(state, current, run_timezone):
            print(
                "SKIP: Horizon Codex already completed on "
                f"{current.date().isoformat()}"
            )
            return 0

        source_report: dict[str, Any] = {}
        try:
            config = _load_and_validate_codex_config(config_path)
            last_success = _parse_timestamp(
                state.get("last_success_at"),
                run_timezone,
            )
            fetch_hours = calculate_fetch_hours(
                config.filtering.time_window_hours,
                current,
                last_success,
            )
            print(
                f"RUN: Horizon Codex {current.date().isoformat()} "
                f"(fetch window: {fetch_hours}h)"
            )

            summaries_before = _summary_snapshot(paths["summaries"])
            source_report = asyncio.run(
                _run_pipeline(config_path, fetch_hours)
            )
            if source_report.get("status") in {"failure", "partial_failure"}:
                raise RuntimeError(
                    "source fetch status was "
                    f"{source_report['status']}"
                )
            summaries_after = _summary_snapshot(paths["summaries"])

            completed_at = _now(run_timezone)
            local_date = completed_at.date().isoformat()
            report_path = paths["reports"] / f"{local_date}.json"
            report = {
                "status": "success",
                "started_at": current.isoformat(),
                "completed_at": completed_at.isoformat(),
                "timezone": str(run_timezone),
                "daily_at": daily_at.strftime("%H:%M"),
                "fetch_hours": fetch_hours,
                "source_report": source_report,
                "summaries": _changed_summaries(
                    summaries_before,
                    summaries_after,
                ),
            }
            _write_json(report_path, report)
            state.update(
                {
                    "last_attempt_at": completed_at.isoformat(),
                    "last_attempt_status": "success",
                    "last_success_at": completed_at.isoformat(),
                    "last_fetch_hours": fetch_hours,
                    "last_report": str(report_path),
                    "last_summaries": report["summaries"],
                }
            )
            state.pop("last_error", None)
            _write_json(paths["state"], state)
            print(f"DONE: report: {report_path}")
            return 0
        except Exception as exc:
            failed_at = _now(run_timezone)
            stamp = failed_at.strftime("%Y%m%dT%H%M%S%f%z")
            report_path = paths["reports"] / f"{stamp}-failure.json"
            report = {
                "status": "failure",
                "started_at": current.isoformat(),
                "completed_at": failed_at.isoformat(),
                "timezone": str(run_timezone),
                "daily_at": daily_at.strftime("%H:%M"),
                "error": f"{type(exc).__name__}: {exc}",
                "source_report": source_report,
            }
            _write_json(report_path, report)
            state.update(
                {
                    "last_attempt_at": failed_at.isoformat(),
                    "last_attempt_status": "failure",
                    "last_error": report["error"],
                    "last_report": str(report_path),
                }
            )
            _write_json(paths["state"], state)
            print(f"FAILED: {report['error']}; report: {report_path}")
            return 1
    finally:
        lock.__exit__(None, None, None)


def _print_status(config_path: Path) -> int:
    state = _load_json(_runner_paths(config_path)["state"])
    if not state:
        print("Horizon Codex has not completed a local daily run yet.")
        return 0
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("data/config.json"),
        help="Horizon configuration path (default: data/config.json)",
    )
    parser.add_argument(
        "--timezone",
        help="IANA timezone (default: the system local timezone)",
    )
    parser.add_argument(
        "--daily-at",
        default="00:00",
        help="Earliest local run time in 24-hour HH:MM format (default: 00:00)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even before daily-at or after today's success",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show the last run status without running",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.status:
        return _print_status(args.config)
    try:
        run_timezone = resolve_timezone(args.timezone)
        daily_at = parse_daily_at(args.daily_at)
    except ValueError as exc:
        parser.error(str(exc))
    return run_once(
        config_path=args.config.expanduser().resolve(),
        run_timezone=run_timezone,
        daily_at=daily_at,
        force=args.force,
    )


if __name__ == "__main__":
    raise SystemExit(main())
