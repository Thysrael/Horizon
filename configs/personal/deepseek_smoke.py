"""Bounded real DeepSeek test; credentials are accepted only on GitHub Actions."""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from configs.personal.check import load_config
from src.ai.client import OpenAIClient
from src.ai.errors import AIProviderUnavailableError
from src.ai.summarizer import DailySummarizer, _safe_url
from src.ai.tokens import get_usage_snapshot, reset_usage
from src.models import AIConfig
from src.orchestrator import HorizonOrchestrator
from src.storage.manager import StorageManager
from src.url_security import safe_request

PRICING_URL = 'https://api-docs.deepseek.com/quick_start/pricing'
MAX_REQUESTS = 16


class SmokeCheckError(RuntimeError):
    """A safe, fixed diagnostic that never contains provider payloads."""



def smoke_config():
    config, profiles = load_config()
    config.ai = AIConfig.model_validate_json((ROOT / 'configs/personal/deepseek-smoke.json').read_text())
    return config, profiles


def choose_candidates(items, limit):
    """Hard cap BEFORE any AI scoring; round-robin through the supplied profiles."""
    if not 1 <= limit <= 5:
        raise ValueError('Candidate limit must be between 1 and 5')
    groups = defaultdict(deque)
    seen = set()
    for item in sorted(items, key=lambda i: i.published_at, reverse=True):
        if item.url in seen or not item.title.strip() or len(item.content or '') < 120:
            continue
        seen.add(item.url)
        groups[str(item.profile)].append(item)
    chosen = []
    while groups and len(chosen) < limit:
        for name in list(groups):
            chosen.append(groups[name].popleft())
            if not groups[name]:
                del groups[name]
            if len(chosen) == limit:
                break
    return chosen


def parse_usd_rates(html, model):
    """Only accept unambiguous per-million USD prices from the official table."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    for table in soup.find_all('table'):
        if not re.search(r'1\s*m(?:illion)?\s*tokens', table.get_text(' ', strip=True), re.I):
            continue
        rows = table.find_all('tr')
        if not rows:
            continue
        header = [c.get_text(' ', strip=True).lower() for c in rows[0].find_all(['th', 'td'])]
        columns = [i for i, text in enumerate(header) if model in text]
        if len(columns) != 1:
            continue
        rates = {}
        for row in rows[1:]:
            cells = [c.get_text(' ', strip=True) for c in row.find_all(['th', 'td'])]
            if len(cells) <= columns[0]:
                continue
            label = cells[0].lower()
            values = re.findall(r'\$\s*(\d+(?:\.\d+)?)', cells[columns[0]])
            if len(values) != 1:
                continue
            key = ('output' if 'output' in label else 'hit' if 'cache hit' in label
                   else 'miss' if 'cache miss' in label else None)
            if key:
                rates[key] = float(values[0])
        if set(rates) == {'hit', 'miss', 'output'}:
            return rates
    return None


class BoundedDeepSeekClient(OpenAIClient):
    def __init__(self, config, report):
        super().__init__(config)
        self.client = self.client.with_options(max_retries=0, timeout=60)
        self.report = report

    async def _do_request(self, **kwargs):
        if self.report['completion_attempts'] >= MAX_REQUESTS:
            raise AIProviderUnavailableError('Smoke test request budget exhausted')
        if len(kwargs['system']) + len(kwargs['user']) > 24000:
            raise AIProviderUnavailableError('Smoke test prompt character budget exceeded')
        kwargs['max_tokens'] = min(kwargs.get('max_tokens') or 2048, 2048)
        self.report['completion_attempts'] += 1
        try:
            response = await super()._do_request(**kwargs)
        except Exception as exc:
            # Do not expose provider response bodies, headers, keys or SDK request details.
            status = getattr(exc, 'status_code', None)
            self.report['api_failure'] = {'type': type(exc).__name__, 'status': status}
            raise AIProviderUnavailableError(f'DeepSeek request stopped (HTTP {status or "unavailable"})') from None
        usage = response.usage
        if usage:
            self.report['response_usage'].append({
                name: getattr(usage, name, None) for name in
                ['prompt_tokens', 'completion_tokens', 'total_tokens',
                 'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens']})
        return response


def finalize_report(report, directory):
    report['usage'] = asdict(get_usage_snapshot())
    report['usage']['total_tokens'] = get_usage_snapshot().total_tokens
    rates = report.get('official_usd_per_million')
    usage = report['response_usage']
    report['estimated_usd'] = None
    if rates and usage and all(u.get('prompt_cache_hit_tokens') is not None
                               and u.get('prompt_cache_miss_tokens') is not None for u in usage):
        report['estimated_usd'] = sum(
            u['prompt_cache_hit_tokens'] * rates['hit']
            + u['prompt_cache_miss_tokens'] * rates['miss']
            + (u['completion_tokens'] or 0) * rates['output'] for u in usage) / 1_000_000
    report['billing_note'] = ('Estimate covers reported response usage only; provider billing is authoritative. '
                              'Missing prices/usage mean unknown, not zero; failed requests may have unreported usage.')
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    summary = ('# Horizon DeepSeek smoke test\n\n'
               f"- Status: {report['status']}\n- Candidates: {report.get('candidate_count', 0)} / 5 maximum\n"
               f"- Selected items: {report.get('selected_count', 0)}\n"
               f"- Completion attempts: {report['completion_attempts']} / {MAX_REQUESTS}\n"
               f"- Reported tokens: {report['usage']['total_tokens']}\n"
               f"- Estimated USD: {report['estimated_usd'] if report['estimated_usd'] is not None else 'unknown (see pricing-reference.txt and report.json)'}\n")
    (directory / 'summary.md').write_text(summary)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
            stream.write(summary)


async def run(limit, directory, report):
    import httpx
    from bs4 import BeautifulSoup
    config, profiles = smoke_config()
    report.update(model=config.ai.model, endpoint=config.ai.base_url, candidate_limit=limit,
                  pricing_source=PRICING_URL)
    runner = HorizonOrchestrator(config, StorageManager(str(directory / 'state')), profiles=profiles)
    items = await runner.fetch_all_sources(datetime.now(timezone.utc) - timedelta(days=7))
    if runner.last_fetch_report:
        report['feed_report'] = runner.last_fetch_report.to_dict()
    candidates = choose_candidates(runner.merge_cross_source_duplicates(items), limit)
    report['candidate_count'] = len(candidates)
    report['candidates'] = [{'id': i.id, 'title': i.title, 'url': i.url,
                             'source': i.metadata.get('feed_name'), 'profile': i.profile} for i in candidates]
    if not candidates:
        raise SmokeCheckError('No usable real RSS candidates; no inference attempted')
    async with httpx.AsyncClient(timeout=20) as client:
        report['links'] = []
        usable = []
        for item in candidates:
            try:
                response = await safe_request(client, 'HEAD', item.url, max_redirects=5)
                if response.status_code in {405, 501}:
                    response = await safe_request(client, 'GET', item.url, max_redirects=5)
                ok = 200 <= response.status_code < 300
                report['links'].append({'url': item.url, 'status': response.status_code, 'ok': ok})
                if ok:
                    usable.append(item)
            except Exception as exc:
                report['links'].append({'url': item.url, 'ok': False, 'error': type(exc).__name__})
        pricing = await client.get(PRICING_URL, follow_redirects=True)
        pricing.raise_for_status()
        text = BeautifulSoup(pricing.text, 'html.parser').get_text(' ', strip=True)
        (directory / 'pricing-reference.txt').write_text(PRICING_URL + '\n' + text)
        report['official_usd_per_million'] = parse_usd_rates(pricing.text, config.ai.model)
    if not usable:
        raise SmokeCheckError('No verified reachable source links; no inference attempted')
    ai = BoundedDeepSeekClient(config.ai, report)
    runner.__dict__['ai_client'] = ai
    try:
        # Read-only metadata request, not a separately billed test completion.
        catalog = await ai.client.models.list()
        report['available_models'] = [model.id for model in catalog.data]
        if config.ai.model not in report['available_models']:
            raise SmokeCheckError('Configured Horizon model alias is absent from the account model catalog')
        analyzed = await runner.analyze_items(usable)
        if any(not i.processing or not i.processing.analysis or i.processing.analysis.score is None for i in analyzed):
            raise SmokeCheckError('One or more candidate analyses failed')
        selected = (await runner.select_digest_items(analyzed)).items
        report['selected_count'] = len(selected)
        if not selected:
            raise SmokeCheckError('No items met the unchanged score threshold; no successful digest claimed')
        result = await runner.enrich_items(selected)
        if result.failed_count:
            raise SmokeCheckError('Enrichment incomplete; no successful digest claimed')
        for item in selected:
            artifact = item.processing.artifacts.get('zh')
            required = {b.id for b in profiles.get(str(item.profile)).definition.enrichment.blocks if not b.optional}
            if not artifact or not required.issubset({b.id for b in artifact.blocks}) or not any('\u4e00' <= c <= '\u9fff' for c in artifact.title):
                raise SmokeCheckError('Chinese artifact contract failed')
            if any(not any('\u4e00' <= c <= '\u9fff' for c in block.content)
                   for block in artifact.blocks if block.id in required):
                raise SmokeCheckError('Required analysis blocks are not Chinese')
        digest = await DailySummarizer(profile_names=profiles.names, profile_order=config.digest.profile_order).generate_summary(
            selected, datetime.now(timezone.utc).strftime('%Y-%m-%d'), len(candidates), language='zh')
        assert len(selected) <= limit <= 5 and config.digest.max_items == 15
        for item in selected:
            if _safe_url(item.url) not in digest or item.metadata.get('feed_name', '') not in digest:
                raise SmokeCheckError('Original link or publisher is missing from rendered digest')
        report['content_checks'] = {'chinese_titles': True, 'required_analysis_blocks': True,
                                    'original_source_links': True, 'selected_links_reachable': True}
        (directory / 'digest-zh.md').write_text(digest)
        report['selected'] = [{'title': i.processing.artifacts['zh'].title, 'url': i.url,
                               'source': i.metadata.get('feed_name'), 'profile': i.profile,
                               'score': i.processing.analysis.score} for i in selected]
        report['status'] = 'success'
    finally:
        await ai.client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=5, choices=range(1, 6))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'status': 'failed', 'completion_attempts': 0, 'response_usage': [],
              'checked_at': datetime.now(timezone.utc).isoformat()}
    reset_usage()
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        if os.getenv('GITHUB_ACTIONS') != 'true':
            raise SmokeCheckError('Real DeepSeek smoke tests are restricted to GitHub Actions')
        if not os.getenv('DEEPSEEK_API_KEY'):
            raise SmokeCheckError('Repository Secret DEEPSEEK_API_KEY is missing')
        asyncio.run(run(args.limit, args.output, report))
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'http_status': getattr(exc, 'status_code', None)}
        if isinstance(exc, SmokeCheckError):
            report['error']['reason'] = str(exc)
        print('Smoke test did not complete; see sanitized report.json. Provider error bodies are not logged.')
    finally:
        finalize_report(report, args.output)
    return 0 if report['status'] == 'success' else 1


if __name__ == '__main__':
    raise SystemExit(main())
