"""Shared CLI helpers for Horizon entrypoints."""

import argparse
import sys
from typing import TYPE_CHECKING

from rich.console import Console

from .storage.manager import ConfigError, StorageManager

if TYPE_CHECKING:  # pragma: no cover
    from .models import Config


def add_log_level_argument(
    parser: argparse.ArgumentParser, default: str = "WARNING"
) -> None:
    parser.add_argument(
        "-l", "--log-level",
        default=default,
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        metavar="LEVEL",
        help=f"Logging level (default: {default})",
    )


def add_data_dir_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-d", "--data-dir",
        default="data",
        metavar="PATH",
        help="Path to the data directory (default: 'data')",
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        metavar="PATH",
        help="Path to config file (default: <data-dir>/config.json)",
    )


def load_config_or_exit(console: Console, args: argparse.Namespace) -> tuple[StorageManager, "Config"]:
    """Open the data directory named by ``-d/-c`` and load config, or exit with a hint."""
    storage = StorageManager(data_dir=args.data_dir, config_path=args.config)
    try:
        return storage, storage.load_config()
    except FileNotFoundError:
        console.print("[bold red]Configuration file not found![/bold red]")
        console.print(
            "Run [bold cyan]uv run horizon-wizard[/bold cyan] to set up your configuration."
        )
        sys.exit(1)
    except ConfigError as e:
        console.print(f"[bold red]Error loading configuration: {e}[/bold red]")
        sys.exit(1)


def default_language(args: argparse.Namespace, config: "Config") -> str:
    """``--lang`` if given, else the first configured AI language."""
    return args.lang or (config.ai.languages[0] if config.ai.languages else "en")
