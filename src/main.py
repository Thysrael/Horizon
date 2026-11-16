"""CLI entry point for Horizon."""

import argparse
import asyncio
import json
import shlex
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from ._cli import add_data_dir_arguments, add_log_level_argument
from .console_icons import get_icons
from .logging_config import configure_logging
from .mcp.errors import HorizonMcpError
from .mcp.service import HorizonPipelineService
from .storage.manager import ConfigError, StorageManager
from .orchestrator import HorizonOrchestrator
from .collection_window import collection_hours
from .models import AIProvider


console = Console(stderr=True)


def print_banner():
    """Print the application banner."""
    banner = r"""
[bold blue]
  _    _            _
 | |  | |          (_)
 | |__| | ___  _ __ _ ___  ___  _ __
 |  __  |/ _ \| '__| |_  / / _ \| '_ \
 | |  | | (_) | |  | |/ / | (_) | | | |
 |_|  |_|\___/|_|  |_/___| \___/|_| |_|
[/bold blue]
[cyan]  AI-Driven Information Aggregation System[/cyan]
    """
    console.print(banner)


def score_main(argv: list[str] | None = None) -> None:
    """Score article URLs and print JSON without publishing a digest."""

    parser = argparse.ArgumentParser(
        prog="horizon score",
        description=(
            "Score one or more article URLs with the same profile analysis path "
            "Horizon uses for digests. Prints JSON to stdout. Does not filter, "
            "enrich, or publish a daily digest. API keys such as DEEPSEEK_API_KEY "
            "stay in the Horizon process environment and are not accepted as arguments."
        ),
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        required=True,
        metavar="URL",
        help="Article URLs to score",
    )
    parser.add_argument(
        "--profile",
        default="reading",
        help="Processing profile id whose analysis.md scores the articles (default: reading)",
    )
    add_data_dir_arguments(parser)
    add_log_level_argument(parser)
    args = parser.parse_args(argv)

    configure_logging(console, level=args.log_level)
    load_dotenv()
    config_path = args.config or str(Path(args.data_dir) / "config.json")

    async def _score():
        service = HorizonPipelineService(console=console)
        return await service.score_urls(
            urls=args.urls,
            profile=args.profile,
            config_path=config_path,
        )

    try:
        payload = asyncio.run(_score())
    except KeyboardInterrupt:
        sys.exit(130)
    except HorizonMcpError as exc:
        payload = {
            "ok": False,
            "error": {"code": exc.code, "message": exc.message, "details": exc.details},
        }
        _print_json(payload)
        sys.exit(1)
    except Exception as exc:
        payload = {
            "ok": False,
            "error": {"code": "HZ_INTERNAL_ERROR", "message": str(exc)},
        }
        _print_json(payload)
        sys.exit(1)

    _print_json(payload)


def _print_json(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _hours_argument(value: str) -> int:
    """Parse the CLI override. Positivity is checked later, once, with the config value."""
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid int value: {value!r}") from exc


def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        score_main(sys.argv[2:])
        return

    configure_logging(console)
    print_banner()
    icons = get_icons()

    parser = argparse.ArgumentParser(
        description="Horizon - AI-Driven Information Aggregation System",
        epilog="Score article URLs without publishing a digest: horizon score --help",
    )
    parser.add_argument("--hours", type=_hours_argument, help="Force fetch from last N hours")
    add_data_dir_arguments(parser)
    add_log_level_argument(parser)
    args = parser.parse_args()

    configure_logging(console, level=args.log_level)

    try:
        # Load environment variables from .env file
        load_dotenv()

        data_dir = Path(args.data_dir)

        # Initialize storage manager
        storage = StorageManager(data_dir=str(data_dir), config_path=args.config)

        # Load configuration
        try:
            config = storage.load_config()
        except FileNotFoundError:
            console.print(
                f"[bold red]{icons['error']} Configuration file not found![/bold red]\n"
            )
            console.print(f"Expected config: [cyan]{storage.config_path}[/cyan]\n")

            example_path = data_dir / "config.example.json"
            if not example_path.exists():
                example_path = Path("data/config.example.json")
            if example_path.exists():
                target_parent = storage.config_path.parent
                if target_parent != Path("."):
                    console.print(
                        f"Create the destination directory:\n"
                        f"  [cyan]mkdir -p {shlex.quote(str(target_parent))}[/cyan]\n"
                    )
                console.print(
                    f"Copy the example config and edit it:\n"
                    f"  [cyan]cp {shlex.quote(str(example_path))} "
                    f"{shlex.quote(str(storage.config_path))}[/cyan]\n"
                )
            if args.config is None and data_dir == Path("data"):
                console.print(
                    "Or run [bold cyan]uv run horizon-wizard[/bold cyan] to launch the interactive setup wizard.\n"
                )
            sys.exit(1)
        except ConfigError as e:
            console.print(
                f"[bold red]{icons['error']} Error loading configuration: {e}[/bold red]"
            )
            sys.exit(1)
        except Exception as e:
            console.print(
                f"[bold red]{icons['error']} Error loading configuration: {e}[/bold red]"
            )
            sys.exit(1)

        icons = get_icons(config.display.icon_style)
        if config.ai.provider == AIProvider.OPENAI_CHATGPT:
            from .ai.chatgpt_auth import MANAGE_USAGE_URL
            console.print(f"Using ChatGPT plan. Manage usage: {MANAGE_USAGE_URL}")

        # Config value and CLI override meet here. The orchestrator receives the int.
        try:
            window = collection_hours(config.collection.time_window_hours, args.hours)
        except ValueError as exc:
            console.print(f"[bold red]{icons['error']} {exc}[/bold red]")
            sys.exit(2)

        orchestrator = HorizonOrchestrator(config, storage, console=console)
        asyncio.run(orchestrator.run(force_hours=window))

    except KeyboardInterrupt:
        console.print(f"\n[yellow]{icons['warning']} Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]{icons['error']} Fatal error: {e}[/bold red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
