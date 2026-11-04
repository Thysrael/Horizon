#!/usr/bin/env python3
"""Validate the personal setup, probe public feeds, or run a guarded digest."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.models import Config
from src.processing.profiles import ProfileRegistry
from src.storage.manager import _expand_env_vars

CONFIG = ROOT / 'configs/personal/config.json'


def load_config() -> tuple[Config, ProfileRegistry]:
    config = Config.model_validate(_expand_env_vars(json.loads(CONFIG.read_text())))
    registry = ProfileRegistry.load(Path(config.processing.profiles_dir),
                                    config.processing.default_profile, base_dir=ROOT)
    registry.validate_source_references(config.sources.model_dump(mode='json'))
    registry.validate_digest_references(config.digest)
    for profile_id in config.processing.profile_settings:
        registry.get(profile_id)
    for profile_id in config.digest.profile_order:
        registry.get(profile_id)
    return config, registry


async def probe_feeds(config: Config) -> int:
    import feedparser
    import httpx
    semaphore = asyncio.Semaphore(4)
    async with httpx.AsyncClient(timeout=20, follow_redirects=True,
                                 headers={'User-Agent': 'Horizon personal feed readiness check'}) as client:
        async def probe(source):
            async with semaphore:
                row = {'name': source.name, 'url': str(source.url)}
                try:
                    response = await client.get(str(source.url))
                    row['status'] = response.status_code
                    response.raise_for_status()
                    feed = feedparser.parse(response.text)
                    if not feed.entries:
                        raise ValueError('No RSS/Atom entries found')
                    usable = [entry for entry in feed.entries if entry.get('title') and entry.get('link')]
                    if not usable:
                        raise ValueError('Feed entries lack titles or original links')
                    row.update(ok=True, entries=len(feed.entries), linked_entries=len(usable))
                except (httpx.HTTPError, ValueError) as exc:
                    # Configured URLs are public and contain no credentials. Do not log bodies/headers.
                    row.update(ok=False, error=type(exc).__name__)
                return row
        rows = await asyncio.gather(*(probe(source) for source in config.sources.rss if source.enabled))
    print(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(), 'feeds': rows},
                     ensure_ascii=False, indent=2))
    return int(any(not row['ok'] for row in rows))


async def collect(config: Config, hours: int) -> int:
    """Run the native RSS scraper without creating any AI client."""
    from datetime import timedelta
    import httpx
    from src.scrapers.rss import RSSScraper
    async with httpx.AsyncClient(timeout=20) as client:
        result = await RSSScraper(config.sources.rss, client).fetch(
            datetime.now(timezone.utc) - timedelta(hours=hours))
    destination = Path('/workspace/horizon-state/personal/raw')
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    path.write_text(json.dumps([item.model_dump(mode='json') for item in result.items],
                               ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result.status, 'successful_feeds': result.successful,
                      'items': len(result.items), 'failed_feeds': list(result.failures),
                      'raw_file': str(path), 'ai_called': False}, ensure_ascii=False, indent=2))
    return int(bool(result.failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'feeds', 'collect', 'run'])
    parser.add_argument('--hours', type=int, default=None,
                        help='One-off collection window; omit for the configured 24 hours')
    args = parser.parse_args()
    config, registry = load_config()
    if args.command == 'validate':
        print(json.dumps({'schema_valid': True, 'profiles': sorted(registry.ids),
                          'languages': config.ai.languages, 'max_items': config.digest.max_items,
                          'model_selected': bool(os.getenv('HORIZON_AI_MODEL')),
                          'enabled_feeds': sum(s.enabled for s in config.sources.rss)},
                         ensure_ascii=False, indent=2))
        return 0
    if args.command == 'feeds':
        return asyncio.run(probe_feeds(config))
    if args.hours is not None and args.hours <= 0:
        parser.error('--hours must be positive')
    if args.command == 'collect':
        return asyncio.run(collect(config, args.hours or config.collection.time_window_hours))
    for name in ['HORIZON_AI_MODEL', 'HORIZON_AI_BASE_URL', 'HORIZON_AI_KEY']:
        if not os.getenv(name, '').strip():
            parser.error(f'Set {name} securely after choosing a provider; no inference was attempted')
    from urllib.parse import urlsplit
    endpoint = urlsplit(config.ai.base_url or '')
    if endpoint.scheme != 'https' or not endpoint.hostname or endpoint.username or endpoint.password:
        parser.error('HORIZON_AI_BASE_URL must be an HTTPS endpoint without embedded credentials')
    command = [str(ROOT / '.venv/bin/horizon'), '--config', str(CONFIG),
               '--data-dir', '/workspace/horizon-state/personal', '--log-level', 'INFO']
    if args.hours is not None:
        command += ['--hours', str(args.hours)]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
