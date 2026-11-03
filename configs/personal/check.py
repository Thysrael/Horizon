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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'feeds', 'run'])
    parser.add_argument('--hours', type=int, default=None,
                        help='One-off collection window; omit for the configured 24 hours')
    args = parser.parse_args()
    config, registry = load_config()
    if args.command == 'validate':
        print(json.dumps({'schema_valid': True, 'profiles': sorted(registry.ids),
                          'languages': config.ai.languages, 'max_items': config.digest.max_items,
                          'model_selected': bool(os.getenv('HORIZON_CHATGPT_MODEL')),
                          'enabled_feeds': sum(s.enabled for s in config.sources.rss)},
                         ensure_ascii=False, indent=2))
        return 0
    if args.command == 'feeds':
        return asyncio.run(probe_feeds(config))
    if args.hours is not None and args.hours <= 0:
        parser.error('--hours must be positive')
    if not os.getenv('HORIZON_CHATGPT_MODEL', '').strip():
        parser.error('Set HORIZON_CHATGPT_MODEL to an exact slug from horizon-chatgpt models; no model is assumed')
    os.environ.setdefault('HORIZON_CHATGPT_AUTH_DIR', '/workspace/horizon-private/chatgpt')
    from src.ai.chatgpt_auth import ChatGPTAuth
    auth = ChatGPTAuth().status(config.ai.chatgpt_account)
    if not auth.get('connected') or not auth.get('plan_usage'):
        parser.error('ChatGPT plan usage is not authorized. Follow configs/personal/README.md; do not paste credentials into chat')
    command = [str(ROOT / '.venv/bin/horizon'), '--config', str(CONFIG),
               '--data-dir', '/workspace/horizon-state/personal', '--log-level', 'INFO']
    if args.hours is not None:
        command += ['--hours', str(args.hours)]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
