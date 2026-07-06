"""CLI entry point for Horizon."""

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from .storage.manager import ConfigError, StorageManager
from .orchestrator import HorizonOrchestrator
from .mcp.run_store import RunStore
from .models import ContentItem


console = Console()


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
    parser.add_argument(
        "--resume",
        type=str,
        metavar="RUN_ID",
        help="Resume a previous run from a saved stage",
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        choices=["raw", "scored", "filtered", "enriched"],
        default="enriched",
        help="Stage to resume from (default: enriched — auto-detect latest)",
    )
    parser.add_argument(
        "--list-runs",
        action="store_true",
        help="List recent checkpointed runs and exit",
    )
    args = parser.parse_args()

    try:
        # Load environment variables from .env file
        load_dotenv()

        # Ensure we're in the project directory or use data/ in current dir
        data_dir = Path("data")

        # Initialize storage manager
        storage = StorageManager(data_dir=str(data_dir))

        # Load configuration
        try:
            config = storage.load_config()
        except FileNotFoundError:
            console.print("[bold red]❌ Configuration file not found![/bold red]\n")
            data_dir_path = data_dir if isinstance(data_dir, Path) else Path(data_dir)
            example_path = data_dir_path / "config.example.json"
            if example_path.exists():
                console.print(
                    f"Copy the example config and edit it:\n"
                    f"  [cyan]cp {example_path} {data_dir_path / 'config.json'}[/cyan]\n"
                )
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

        # Initialize run store for checkpoints
        runs_root = data_dir if isinstance(data_dir, Path) else Path(data_dir)
        runs_root = runs_root / "mcp-runs"
        run_store = RunStore(runs_root)

        # Handle --list-runs
        if args.list_runs:
            runs = run_store.list_runs(limit=20)
            if not runs:
                console.print("[yellow]No checkpointed runs found.[/yellow]")
            else:
                console.print("[bold]Recent checkpointed runs:[/bold]\n")
                for r in runs:
                    stages = []
                    for s in ("raw", "scored", "filtered", "enriched"):
                        if run_store.has_stage(r["run_id"], s):
                            stages.append(s)
                    console.print(
                        f"  [cyan]{r['run_id']}[/cyan] — {r.get('created_at', '?')[:19]}\n"
                        f"    stages: {', '.join(stages) if stages else 'none'}"
                    )
            sys.exit(0)

        # --resume: load from saved stage and continue
        if args.resume:
            resume_run_id = args.resume
            resume_stage = args.resume_from

            # Auto-detect latest available stage if not specified or enriched not found
            if resume_stage == "enriched" and not run_store.has_stage(resume_run_id, "enriched"):
                for auto_stage in ("filtered", "scored", "raw"):
                    if run_store.has_stage(resume_run_id, auto_stage):
                        resume_stage = auto_stage
                        console.print(
                            f"[yellow]⚠️  Stage 'enriched' not found, auto-detected: {auto_stage}[/yellow]"
                        )
                        break

            if not run_store.has_stage(resume_run_id, resume_stage):
                available = []
                for s in ("raw", "scored", "filtered", "enriched"):
                    if run_store.has_stage(resume_run_id, s):
                        available.append(s)
                console.print(
                    f"[bold red]❌ Stage '{resume_stage}' not found in run {resume_run_id}[/bold red]"
                )
                if available:
                    console.print(f"   Available stages: {', '.join(available)}")
                sys.exit(1)

            console.print(
                f"📂 Loading {resume_stage} items from run {resume_run_id}..."
            )
            payload = run_store.load_items(resume_run_id, resume_stage)
            items = [ContentItem.model_validate(d) for d in payload]

            # Get total fetched from raw stage for summary context
            total_fetched = len(items)
            if run_store.has_stage(resume_run_id, "raw"):
                try:
                    total_fetched = len(run_store.load_items(resume_run_id, "raw"))
                except Exception:
                    pass
            elif run_store.has_stage(resume_run_id, "scored"):
                try:
                    total_fetched = len(run_store.load_items(resume_run_id, "scored"))
                except Exception:
                    pass

            console.print(f"   Loaded {len(items)} items\n")

            orchestrator = HorizonOrchestrator(config, storage)
            asyncio.run(
                orchestrator.resume_from(
                    items=items,
                    stage=resume_stage,
                    all_fetched=total_fetched,
                    run_store=run_store,
                    run_id=resume_run_id,
                )
            )
            return

        # Create and run orchestrator with checkpointing
        run_id = run_store.create_run()
        console.print(f"[dim]Checkpoint run: {run_id}[/dim]\n")

        orchestrator = HorizonOrchestrator(config, storage)
        asyncio.run(orchestrator.run(
            force_hours=args.hours,
            run_store=run_store,
            run_id=run_id,
        ))

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Fatal error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
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
    "time_window_hours": 24
  }
}

Also create a .env file with:
ANTHROPIC_API_KEY=your_api_key_here
GITHUB_TOKEN=your_github_token_here (optional but recommended)
"""
    console.print(template)


if __name__ == "__main__":
    main()
