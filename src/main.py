"""CLI entry point for Horizon."""

import argparse
import asyncio
import shlex
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from ._cli import add_data_dir_arguments, add_log_level_argument
from .console_icons import get_icons
from .logging_config import configure_logging
from .storage.manager import ConfigError, StorageManager
from .orchestrator import HorizonOrchestrator
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


def main():
    """Main CLI entry point."""
    configure_logging(console)
    print_banner()
    icons = get_icons()

    parser = argparse.ArgumentParser(description="Horizon - AI-Driven Information Aggregation System")
    parser.add_argument("--hours", type=int, help="Force fetch from last N hours")
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

        # Create and run orchestrator
        orchestrator = HorizonOrchestrator(config, storage, console=console)
        asyncio.run(orchestrator.run(force_hours=args.hours))

    except KeyboardInterrupt:
        console.print(f"\n[yellow]{icons['warning']} Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]{icons['error']} Fatal error: {e}[/bold red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
