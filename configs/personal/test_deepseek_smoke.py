"""No credentials or real requests: enforce candidate, request and billing contracts."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from configs.personal import deepseek_smoke as smoke
from src.ai.errors import AIProviderUnavailableError
from src.models import ContentItem, SourceType


def make_item(index, profile='world-affairs'):
    return ContentItem(id=f'rss:{index}', source_type=SourceType.RSS, title=f'Article {index}',
                       url=f'https://example.com/{index}', content='Public source material. ' * 20,
                       published_at=datetime.now(timezone.utc), profile=profile)


def test_candidate_cap_is_before_scoring_and_round_robins_profiles():
    items = [make_item(i, f'profile-{i % 6}') for i in range(60)]
    chosen = smoke.choose_candidates(items, 5)
    assert len(chosen) == len({item.profile for item in chosen}) == 5
    for invalid in [0, 6, -1]:
        with pytest.raises(ValueError):
            smoke.choose_candidates(items, invalid)


def test_duplicate_links_and_insufficient_material_are_not_scored():
    good = make_item(1)
    short = make_item(2).model_copy(update={'content': 'too short'})
    assert smoke.choose_candidates([good, good.model_copy(), short], 5) == [good]


def test_deepseek_overlay_preserves_personal_rules():
    config, profiles = smoke.smoke_config()
    assert config.ai.provider.value == 'deepseek'
    assert config.ai.model == 'deepseek-chat'
    assert config.ai.api_key_env == 'DEEPSEEK_API_KEY'
    assert config.ai.base_url == 'https://api.deepseek.com'
    assert config.ai.languages == ['zh'] and config.digest.max_items == 15
    assert len(profiles.ids) == 6
    assert all(not block.tools for p in profiles.profiles for block in p.definition.enrichment.blocks)


def test_budget_stops_before_an_additional_request():
    client = smoke.BoundedDeepSeekClient.__new__(smoke.BoundedDeepSeekClient)
    client.report = {'completion_attempts': smoke.MAX_REQUESTS}
    with pytest.raises(AIProviderUnavailableError):
        asyncio.run(client._do_request(system='test', user='test'))


def test_official_price_parser_requires_model_and_usd_units():
    table = ('<table><tr><th>MODEL</th><th>deepseek-chat</th></tr>'
             '<tr><td>1M TOKENS INPUT (CACHE HIT)</td><td>$0.01</td></tr>'
             '<tr><td>1M TOKENS INPUT (CACHE MISS)</td><td>$0.10</td></tr>'
             '<tr><td>1M TOKENS OUTPUT</td><td>$0.20</td></tr></table>')
    assert smoke.parse_usd_rates(table, 'deepseek-chat') == {'hit': .01, 'miss': .10, 'output': .20}
    assert smoke.parse_usd_rates(table, 'unavailable-model') is None
    assert smoke.parse_usd_rates(table.replace('$', '¥'), 'deepseek-chat') is None


def test_no_inference_outside_actions(monkeypatch, tmp_path):
    monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
    monkeypatch.setattr(sys, 'argv', ['smoke', '--output', str(tmp_path)])
    def forbidden(*args, **kwargs):
        raise AssertionError('Must not run or request credentials outside Actions')
    monkeypatch.setattr(smoke, 'run', forbidden)
    assert smoke.main() == 1
    import json
    report = json.loads((tmp_path / 'report.json').read_text())
    assert report['completion_attempts'] == 0
    assert report['status'] == 'failed'
    assert 'restricted to GitHub Actions' in report['error']['reason']


def test_fee_estimate_uses_reported_cache_and_output_usage(monkeypatch, tmp_path):
    import json
    from src.ai.tokens import record_usage, reset_usage
    monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
    reset_usage()
    record_usage('deepseek', 1_000_000, 100_000)
    report = {'status': 'success', 'completion_attempts': 1,
              'official_usd_per_million': {'hit': .01, 'miss': .10, 'output': .20},
              'response_usage': [{'prompt_cache_hit_tokens': 500_000,
                                  'prompt_cache_miss_tokens': 500_000,
                                  'completion_tokens': 100_000}]}
    smoke.finalize_report(report, tmp_path)
    saved = json.loads((tmp_path / 'report.json').read_text())
    assert saved['estimated_usd'] == pytest.approx(.075)
    assert saved['usage']['total_tokens'] == 1_100_000
    reset_usage()


def test_output_token_limit_cannot_be_overridden(monkeypatch):
    captured = {}
    async def fake_request(self, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=10,
                                                     total_tokens=110))
    monkeypatch.setattr(smoke.OpenAIClient, '_do_request', fake_request)
    client = smoke.BoundedDeepSeekClient.__new__(smoke.BoundedDeepSeekClient)
    client.report = {'completion_attempts': 0, 'response_usage': []}
    asyncio.run(client._do_request(system='synthetic', user='synthetic', max_tokens=9000))
    assert captured['max_tokens'] == 2048
    assert client.report['completion_attempts'] == 1


@pytest.mark.parametrize('status', ['success', 'failed'])
def test_report_serializes_nested_pydantic_urls_and_other_supported_types(monkeypatch, tmp_path, status):
    import json
    from src.ai.tokens import ProviderUsage, reset_usage
    monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
    reset_usage()
    item = make_item(1)
    report = {'status': status, 'completion_attempts': 0, 'response_usage': [],
              'candidates': [{'url': item.url}], 'links': [{'url': item.url}],
              'selected': [{'url': item.url}],
              'nested': {'item': item, 'timestamp': item.published_at,
                         'path': tmp_path, 'source_type': SourceType.RSS,
                         'usage_dataclass': ProviderUsage(input_tokens=2, output_tokens=3)},
              'note': '中文报告'}
    smoke.finalize_report(report, tmp_path)
    saved = json.loads((tmp_path / 'report.json').read_text())
    for field in ['candidates', 'links', 'selected']:
        assert saved[field][0]['url'] == item.model_dump(mode='json')['url']
        assert isinstance(saved[field][0]['url'], str)
    assert saved['nested']['item'] == item.model_dump(mode='json')
    assert isinstance(saved['nested']['timestamp'], str)
    assert saved['nested']['path'] == str(tmp_path)
    assert saved['nested']['source_type'] == 'rss'
    assert saved['nested']['usage_dataclass'] == {'input_tokens': 2, 'output_tokens': 3}
    assert '中文报告' in (tmp_path / 'report.json').read_text()
    assert (tmp_path / 'summary.md').is_file()


def test_link_check_converts_httpurl_before_safe_request(monkeypatch, tmp_path):
    from src.orchestrator import HorizonOrchestrator
    item = make_item(1)
    async def fetch(self, since):
        return [item]
    checked = []
    async def safe_request(client, method, url, **kwargs):
        assert isinstance(url, str)
        checked.append((method, url))
        return SimpleNamespace(status_code=200)
    async def stop_before_any_model_request(self, url, **kwargs):
        assert url == smoke.PRICING_URL
        raise smoke.SmokeCheckError('Synthetic stop before model initialization')
    import httpx
    monkeypatch.setattr(HorizonOrchestrator, 'fetch_all_sources', fetch)
    monkeypatch.setattr(smoke, 'safe_request', safe_request)
    monkeypatch.setattr(httpx.AsyncClient, 'get', stop_before_any_model_request)
    report = {'completion_attempts': 0, 'response_usage': []}
    with pytest.raises(smoke.SmokeCheckError, match='Synthetic stop'):
        asyncio.run(smoke.run(5, tmp_path, report))
    assert checked == [('HEAD', str(item.url))]
    assert report['links'][0]['ok'] is True
    assert report['completion_attempts'] == 0
