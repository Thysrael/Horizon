"""Interactive setup wizard for Horizon configuration."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

from ..models import (
    AIConfig, AIProvider, AI_PROVIDER_DEFAULTS, Config, FilteringConfig, SourcesConfig,
    GitHubSourceConfig, HackerNewsConfig, RSSSourceConfig,
    RedditConfig, RedditSubredditConfig, RedditUserConfig,
    TelegramConfig, TelegramChannelConfig,
)
from ..storage.manager import StorageManager
from .presets import load_presets, match_sources


console = Console()


def print_banner():
    """Print the setup wizard banner."""
    banner = r"""
[bold blue]
  _    _            _
 | |  | |          (_)
 | |__| | ___  _ __ _ ___  ___  _ __
 |  __  |/ _ \| '__| |_  / / _ \| '_ \
 | |  | | (_) | |  | |/ / | (_) | | | |
 |_|  |_|\___/|_|  |_/___| \___/|_| |_|
[/bold blue]
[cyan]  Setup Wizard — Configure your information sources[/cyan]
    """
    console.print(banner)


def configure_ai() -> Optional[AIConfig]:
    """Step 1: Configure AI provider.

    Returns:
        AIConfig if configured, None if user skips.
    """
    console.print("\n[bold]Step 1: AI Configuration[/bold]\n")

    # Check for existing .env
    load_dotenv()

    providers = [p.value for p in AIProvider]
    console.print(f"Available providers: {', '.join(providers)}")
    provider = Prompt.ask(
        "AI provider",
        choices=providers,
        default="openai",
    )
    provider_enum = AIProvider(provider)

    provider_defaults = AI_PROVIDER_DEFAULTS.get(provider_enum, {})
    model = Prompt.ask("Model name", default=provider_defaults.get("model", ""))

    if provider_enum == AIProvider.OLLAMA:
        base_url = Prompt.ask(
            "Ollama base URL (leave empty for http://localhost:11434)",
            default="",
        )
    else:
        base_url = Prompt.ask("Base URL (leave empty for default)", default="")

    # Determine default env var name
    api_key_env = Prompt.ask(
        "API key environment variable name",
        default=provider_defaults.get("api_key_env", "API_KEY"),
    )

    # Check if the key is actually set
    if api_key_env and not os.getenv(api_key_env):
        console.print(
            f"[yellow]⚠  {api_key_env} is not set in environment or .env file.[/yellow]"
        )
        console.print("   AI features (smart recommendations) will be skipped.")
        console.print(f"   Add it to your .env file later: {api_key_env}=your_key_here\n")

    languages = Prompt.ask(
        "Output languages (comma-separated)",
        default="zh,en",
    )
    lang_list = [l.strip() for l in languages.split(",") if l.strip()]

    return AIConfig(
        provider=provider_enum,
        model=model,
        base_url=base_url or None,
        api_key_env=api_key_env,
        temperature=0.3,
        max_tokens=8192,
        languages=lang_list,
    )


def _ai_recommendations_available(ai_config: AIConfig) -> bool:
    if ai_config.provider in {AIProvider.CODEX, AIProvider.OLLAMA}:
        return True
    return bool(ai_config.api_key_env and os.getenv(ai_config.api_key_env))


def get_interests() -> str:
    """Step 2: Get user's interest description.

    Returns:
        Free-form interest string.
    """
    console.print("\n[bold]Step 2: Describe Your Interests[/bold]\n")
    console.print(
        "Describe what topics you'd like to follow. "
        "You can use Chinese, English, or both.\n"
        "[dim]Examples: \"LLM inference\", \"具身智能\", \"Rust systems programming\", "
        "\"web security\", \"开源工具\"[/dim]\n"
    )
    interests = Prompt.ask("Your interests")
    return interests


def select_sources(
    preset_sources: List[Dict],
    ai_sources: List[Dict],
) -> List[Dict]:
    """Step 5: Interactive source selection with a rich table.

    Args:
        preset_sources: Sources matched from presets.
        ai_sources: Sources recommended by AI.

    Returns:
        List of selected source dicts.
    """
    all_sources = preset_sources + ai_sources
    if not all_sources:
        console.print("[yellow]No sources matched your interests.[/yellow]")
        return []

    # Display the recommendation table
    console.print("\n[bold]Step 3: Review Recommended Sources[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Type", width=12)
    table.add_column("Description", min_width=30)
    table.add_column("Origin", width=8)
    table.add_column("Enabled", justify="center", width=7)

    enabled = [True] * len(all_sources)

    for i, src in enumerate(all_sources):
        origin_style = "green" if src.get("origin") == "preset" else "cyan"
        table.add_row(
            str(i + 1),
            src.get("type", "?"),
            src.get("description", ""),
            f"[{origin_style}]{src.get('origin', '?')}[/{origin_style}]",
            "✓",
        )

    console.print(table)

    # Let user toggle
    console.print(
        "\n[dim]Enter numbers to toggle off/on (e.g. '3 5 7'), or press Enter to accept all:[/dim]"
    )
    toggle_input = Prompt.ask("Toggle", default="").strip()

    if toggle_input:
        for num_str in toggle_input.split():
            try:
                idx = int(num_str) - 1
                if 0 <= idx < len(enabled):
                    enabled[idx] = not enabled[idx]
            except ValueError:
                pass

    selected = [src for src, on in zip(all_sources, enabled) if on]
    console.print(f"\n[green]✓ {len(selected)} sources selected[/green]")
    return selected


def build_config(
    ai_config: AIConfig,
    selected_sources: List[Dict],
) -> Config:
    """Step 6: Assemble the final Config object.

    Args:
        ai_config: AI configuration.
        selected_sources: List of selected source dicts.

    Returns:
        Complete Config object.
    """
    github_sources = []
    rss_sources = []
    reddit_subreddits = []
    reddit_users = []
    telegram_channels = []
    hn_enabled = False

    for src in selected_sources:
        src_type = src.get("type", "")
        cfg = src.get("config", {})

        if src_type == "github_user":
            github_sources.append(GitHubSourceConfig(
                type="user_events",
                username=cfg.get("username", ""),
                enabled=True,
            ))
        elif src_type == "github_repo":
            github_sources.append(GitHubSourceConfig(
                type="repo_releases",
                owner=cfg.get("owner", ""),
                repo=cfg.get("repo", ""),
                enabled=True,
            ))
        elif src_type == "rss":
            rss_sources.append(RSSSourceConfig(
                name=cfg.get("name", ""),
                url=cfg.get("url", ""),
                enabled=True,
                category=cfg.get("category", ""),
            ))
        elif src_type == "reddit_subreddit":
            reddit_subreddits.append(RedditSubredditConfig(
                subreddit=cfg.get("subreddit", ""),
                sort=cfg.get("sort", "hot"),
                fetch_limit=cfg.get("fetch_limit", 15),
                min_score=cfg.get("min_score", 50),
            ))
        elif src_type == "reddit_user":
            reddit_users.append(RedditUserConfig(
                username=cfg.get("username", ""),
            ))
        elif src_type == "telegram":
            telegram_channels.append(TelegramChannelConfig(
                channel=cfg.get("channel", ""),
                fetch_limit=cfg.get("fetch_limit", 20),
            ))
        elif src_type == "hackernews":
            hn_enabled = True

    # Keep HackerNews as the fallback when no recommendation was selected.
    hn_config = HackerNewsConfig(
        enabled=hn_enabled or not selected_sources,
        fetch_top_stories=30,
        min_score=100,
    )

    reddit_config = RedditConfig(
        enabled=bool(reddit_subreddits or reddit_users),
        subreddits=reddit_subreddits,
        users=reddit_users,
        fetch_comments=10,
    )

    telegram_config = TelegramConfig(
        enabled=bool(telegram_channels),
        channels=telegram_channels,
    )

    sources = SourcesConfig(
        github=github_sources,
        hackernews=hn_config,
        rss=rss_sources,
        reddit=reddit_config,
        telegram=telegram_config,
    )

    filtering = FilteringConfig(
        ai_score_threshold=7.0,
        time_window_hours=24,
    )

    return Config(
        version="1.0",
        ai=ai_config,
        sources=sources,
        filtering=filtering,
    )


def merge_configs(new_config: Config, existing_config: Config) -> Config:
    """Merge new config into existing config, deduplicating sources.

    Rules:
    - ai / filtering: use new values (full replacement)
    - sources: deduplicate by unique key, append new ones
    - existing enabled=false sources are preserved

    Args:
        new_config: Newly generated config.
        existing_config: Existing config to merge into.

    Returns:
        Merged Config object.
    """
    merged = existing_config.model_copy(deep=True)
    merged.ai = new_config.ai.model_copy(deep=True)
    merged.filtering = new_config.filtering.model_copy(deep=True)

    merged.sources.github = _merge_source_list(
        new_config.sources.github, existing_config.sources.github, _gh_key
    )
    merged.sources.rss = _merge_source_list(
        new_config.sources.rss, existing_config.sources.rss, lambda source: str(source.url)
    )
    merged.sources.reddit.subreddits = _merge_source_list(
        new_config.sources.reddit.subreddits,
        existing_config.sources.reddit.subreddits,
        lambda source: source.subreddit,
    )
    merged.sources.reddit.users = _merge_source_list(
        new_config.sources.reddit.users,
        existing_config.sources.reddit.users,
        lambda source: source.username,
    )
    merged.sources.telegram.channels = _merge_source_list(
        new_config.sources.telegram.channels,
        existing_config.sources.telegram.channels,
        lambda source: source.channel,
    )

    return merged


def _merge_source_list(new_sources, existing_sources, key):
    """Merge and deduplicate sources without replacing existing settings."""
    merged_by_key = {}
    for source in existing_sources or []:
        source_key = key(source)
        merged_by_key.setdefault(source_key, source.model_copy(deep=True))
    for source in new_sources or []:
        source_key = key(source)
        merged_by_key.setdefault(source_key, source.model_copy(deep=True))
    return list(merged_by_key.values())


def _gh_key(src: GitHubSourceConfig) -> str:
    """Generate unique key for a GitHub source."""
    if src.type == "user_events":
        return f"user:{src.username}"
    return f"repo:{src.owner}/{src.repo}"


def main():
    """Main entry point for the setup wizard."""
    print_banner()

    storage = StorageManager(data_dir="data")

    # Step 1: AI configuration
    ai_config = configure_ai()
    if ai_config is None:
        console.print("[red]Setup cancelled.[/red]")
        sys.exit(0)

    # Step 2: Interest description
    interests = get_interests()

    # Step 3: Preset library matching
    console.print("\n[dim]Fetching preset source library...[/dim]")
    try:
        presets = load_presets(prefer_api=True)
        offline = os.environ.get("HORIZON_OFFLINE", "").lower() in ("1", "true", "yes")
        if offline:
            console.print("[dim]Using local presets (offline mode)[/dim]")
        else:
            console.print("[dim]Loaded preset sources from API[/dim]")
    except FileNotFoundError:
        console.print("[yellow]Could not fetch presets (offline and no local file).[/yellow]")
        console.print("[yellow]Skipping preset matching.[/yellow]")
        presets = {"domains": []}

    matched_sources = match_sources(interests, presets)
    preset_sources = [src for src, _ in matched_sources]

    if matched_sources:
        console.print(f"[green]Found {len(preset_sources)} matching sources[/green]")
    else:
        console.print("[yellow]No preset sources matched — AI will try to recommend.[/yellow]")

    # Step 4: AI recommendations (optional)
    ai_sources = []
    ai_available = _ai_recommendations_available(ai_config)

    if ai_available:
        if Confirm.ask("\nAsk AI for additional source recommendations?", default=True):
            console.print("[dim]Asking AI for recommendations...[/dim]")
            from .ai_recommend import get_ai_recommendations_sync

            ai_sources = get_ai_recommendations_sync(ai_config, interests, preset_sources)
            if ai_sources:
                console.print(f"[green]AI recommended {len(ai_sources)} additional sources[/green]")
            else:
                console.print("[yellow]AI returned no additional recommendations.[/yellow]")
    else:
        console.print(
            f"\n[dim]Skipping AI recommendations ({ai_config.api_key_env} not set)[/dim]"
        )

    # Step 5: Interactive source selection
    selected = select_sources(preset_sources, ai_sources)

    if not selected:
        console.print("[yellow]No sources selected. Adding HackerNews as default.[/yellow]")

    # Step 6: Build config
    config = build_config(ai_config, selected)

    # Merge with existing config if present
    try:
        existing = storage.load_config()
        if Confirm.ask("\nExisting config.json found. Merge new sources into it?", default=True):
            config = merge_configs(config, existing)
    except FileNotFoundError:
        pass

    # Save
    path = storage.save_config(config, backup=True)

    # Summary
    console.print(Panel(
        f"[green]✓ Configuration saved to {path}[/green]\n\n"
        f"  AI:      {ai_config.provider.value} / {ai_config.model}\n"
        f"  Sources: {_count_sources(config)} total\n"
        f"  Threshold: {config.filtering.ai_score_threshold}\n\n"
        f"Run [bold cyan]horizon[/bold cyan] to start aggregating!",
        title="Setup Complete",
        border_style="green",
    ))


def _count_sources(config: Config) -> int:
    """Count total number of enabled sources."""
    count = 0
    count += len([s for s in config.sources.github if s.enabled])
    if config.sources.hackernews.enabled:
        count += 1
    count += len([s for s in config.sources.rss if s.enabled])
    if config.sources.reddit.enabled:
        count += len([s for s in config.sources.reddit.subreddits if s.enabled])
        count += len([s for s in config.sources.reddit.users if s.enabled])
    if config.sources.telegram.enabled:
        count += len([s for s in config.sources.telegram.channels if s.enabled])
    if config.sources.twitter and config.sources.twitter.enabled:
        count += len(config.sources.twitter.users)
    if config.sources.openbb and config.sources.openbb.enabled:
        count += len([s for s in config.sources.openbb.watchlists if s.enabled])
    if config.sources.ossinsight.enabled:
        count += 1
    if config.sources.gdelt and config.sources.gdelt.enabled:
        count += 1
    if config.sources.google_news and config.sources.google_news.enabled:
        count += 1
    return count
