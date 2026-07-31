"""CLI entry point for Horizon."""

import argparse
import asyncio
import logging
import shlex
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from .storage.manager import ConfigError, StorageManager
from .orchestrator import HorizonOrchestrator


console = Console(stderr=True)
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[RichHandler(console=console, show_path=False)],
)
logger = logging.getLogger(__name__)


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
    print_banner()

    parser = argparse.ArgumentParser(description="Horizon - AI-Driven Information Aggregation System")
    parser.add_argument("--hours", type=int, help="Force fetch from last N hours")
    parser.add_argument("-d", "--data-dir", default="data", metavar="PATH",
                        help="Path to the data directory (default: 'data')")
    parser.add_argument("-c", "--config", default=None, metavar="PATH",
                        help="Path to config file (default: <data-dir>/config.json)")
    args = parser.parse_args()

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
            console.print("[bold red]❌ Configuration file not found![/bold red]\n")
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
            console.print(f"[bold red]❌ Error loading configuration: {e}[/bold red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]❌ Error loading configuration: {e}[/bold red]")
            sys.exit(1)

        # Create and run orchestrator
        orchestrator = HorizonOrchestrator(config, storage, console=console)
        asyncio.run(orchestrator.run(force_hours=args.hours))

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Fatal error: {e}[/bold red]")
        console.print_exception()
        sys.exit(1)


def print_config_template():
    """Print configuration template."""
    template = """
{
  "version": "1.0",
  "ai": {
    "provider": "anthropic",
    "model": "claude-sonnet-4.5-20250929",
    "api_key_env": "ANTHROPIC_API_KEY",
    "temperature": 0.3,
    "max_tokens": 4096
  },
  "sources": {
    "github": [
      {
        "type": "user_events",
        "username": "torvalds",
        "enabled": true
      }
    ],
    "hackernews": {
      "enabled": true,
      "fetch_top_stories": 30,
      "min_score": 100
    },
    "rss": [
      {
        "name": "Example Blog",
        "url": "https://example.com/feed.xml",
        "enabled": true,
        "category": "software-engineering"
      }
    ]
  },
  "filtering": {
    "ai_score_threshold": 7.0,
    "time_window_hours": 24,
    "max_items": null,
    "category_groups": {},
    "default_group": "other",
    "default_group_limit": null
  }
}

Also create a .env file with:
ANTHROPIC_API_KEY=your_api_key_here
GITHUB_TOKEN=your_github_token_here (optional but recommended)
"""
    console.print(template)


if __name__ == "__main__":
    main()
