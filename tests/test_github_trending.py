"""Official daily ranking order, failure reporting, and digest integration."""
import asyncio
from datetime import datetime, timezone
from io import StringIO
import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError
from rich.console import Console

from src.ai.summarizer import DailySummarizer
from src.mcp.service import HorizonPipelineService
from src.models import (
    ClassificationResult, Config, ContentAnalysis, ContentArtifact, ContentBlock,
    ContentItem, GitHubSourceConfig, ProcessingResult, SourceType,
)
from src.orchestrator import HorizonOrchestrator
from src.scrapers.github import GitHubScraper
from src.storage.manager import StorageManager

ROOT = Path(__file__).resolve().parents[1]
SINCE = datetime(2099, 1, 1, tzinfo=timezone.utc)


def ranking_html():
    return ''.join(
        f'<article class="Box-row"><h2><a href="/owner/repo{n}">owner / repo{n}</a></h2>'
        + (f'<p>Project {n} description.</p>' if n != 2 else '')
        + ('<span itemprop="programmingLanguage">Python</span>' if n != 3 else '')
        + (f'<span class="d-inline-block float-sm-right">{n},001 stars today</span>' if n != 4 else '')
        + '</article>' for n in range(1, 7)
    )


def collect(html=None, source=None, status=200):
    requests = []
    def reply(request):
        requests.append(request)
        return httpx.Response(status, text=ranking_html() if html is None else html)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(reply)) as client:
            return await GitHubScraper([source or GitHubSourceConfig(type='trending')], client).fetch(SINCE)
    return asyncio.run(run()), requests


def snapshots():
    return collect()[0].items


def config():
    return Config.model_validate({
        'ai': {'provider': 'openai', 'model': 'test', 'api_key_env': 'UNUSED_TEST_KEY', 'languages': ['en', 'zh']},
        'sources': {'github': [{'type': 'trending'}]},
        'processing': {'profiles_dir': str(ROOT/'profiles'), 'default_profile': 'tech-news'},
        'digest': {'max_items': 1},
    })


def news(key, score=9):
    return ContentItem(id=key, source_type=SourceType.RSS, title=key,
        url=f'https://example.com/{key}', published_at=datetime.now(timezone.utc),
        profile='tech-news', processing=ProcessingResult(
            classification=ClassificationResult(profile='tech-news', method='source_override'),
            analysis=ContentAnalysis(score=score, reason='evidence', summary='Verified news.'),
            artifacts={lang: ContentArtifact(language=lang, title=key, blocks=[ContentBlock(
                id='summary', title='Summary', primary=True, content='Verified news summary.')]) for lang in ['en', 'zh']},
        ))


def forbid_model(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError('Trending snapshots must not initialize a model client')
    monkeypatch.setattr('src.orchestrator.create_ai_client', fail)


def test_default_top_five_preserves_page_order_instead_of_star_order(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'never-send-this-token-to-the-public-page')
    result, requests = collect(source=GitHubSourceConfig(type='trending', category='oss', profile='tech-news'))
    assert [x.title for x in result.items] == [f'owner/repo{n}' for n in range(1, 6)]
    assert [x.metadata['rank'] for x in result.items] == [1, 2, 3, 4, 5]
    assert [x.id for x in result.items] == [f'github:trending:owner/repo{n}' for n in range(1, 6)]
    assert result.items[0].metadata['stars_today'] == 1001
    assert result.items[0].metadata['category'] == 'oss'
    assert result.items[0].profile == 'tech-news'
    assert result.items[0].metadata['language'] == 'Python'
    assert result.status == 'success'
    assert str(requests[0].url) == 'https://github.com/trending?since=daily'
    assert 'Authorization' not in requests[0].headers
    # Even a future `since` does not filter a current ranking snapshot.
    assert all(x.published_at < SINCE and x.published_at.tzinfo is not None for x in result.items)
    assert len({x.metadata['observed_at'] for x in result.items}) == 1
    assert result.items[0].published_at == datetime.fromisoformat(result.items[0].metadata['observed_at'])


def test_optional_description_language_and_stars_may_be_missing():
    result, _ = collect()
    assert result.items[1].content == ''
    assert result.items[2].metadata['language'] is None
    assert result.items[3].metadata['stars_today'] is None


@pytest.mark.parametrize('limit', [1, 3, 6])
def test_configurable_rank_limit(limit):
    result, _ = collect(source=GitHubSourceConfig(type='trending', fetch_limit=limit))
    assert len(result.items) == limit


@pytest.mark.parametrize('limit', [0, 26])
def test_invalid_rank_limits_are_rejected(limit):
    with pytest.raises(ValidationError):
        GitHubSourceConfig(type='trending', fetch_limit=limit)


@pytest.mark.parametrize('html', ['<p>Sign in</p>', ranking_html().replace('class="Box-row"', 'class="changed"'), ranking_html().replace('/owner/repo2', 'https://evil.example/repo')])
def test_changed_or_invalid_page_reports_failure_instead_of_a_fake_ranking(html):
    result, _ = collect(html)
    assert result.items == []
    assert result.status == 'failure'
    assert 'trending/daily' in result.failures


def test_short_page_and_http_error_are_failures():
    result, _ = collect(source=GitHubSourceConfig(type='trending', fetch_limit=7))
    assert result.status == 'failure'
    result, _ = collect(status=403)
    assert result.status == 'failure'
    assert '403' in result.failures['trending/daily']


def test_disabled_source_does_not_make_requests():
    result, requests = collect(source=GitHubSourceConfig(type='trending', enabled=False))
    assert result.items == []
    assert requests == []


def test_trending_failure_preserves_independent_release_results():
    def reply(request):
        if request.url.host == 'github.com':
            return httpx.Response(503)
        return httpx.Response(200, json=[{'id': 1, 'tag_name': 'v1', 'name': 'Release',
            'html_url': 'https://github.com/owner/repo/releases/tag/v1', 'body': 'New release',
            'published_at': '2026-11-01T00:00:00Z', 'author': {'login': 'owner'}}])
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(reply)) as client:
            return await GitHubScraper([GitHubSourceConfig(type='trending'), GitHubSourceConfig(type='repo_releases', owner='owner', repo='repo')], client).fetch(datetime(2026, 1, 1, tzinfo=timezone.utc))
    result = asyncio.run(run())
    assert result.status == 'partial_failure'
    assert len(result.items) == 1
    assert not result.items[0].metadata.get('github_trending')


@pytest.mark.parametrize('language,heading', [('en', 'GitHub Daily Trending Top 5'), ('zh', 'GitHub 每日热门 Top 5')])
def test_ranking_only_summary_has_no_false_empty_news_or_scores(language, heading):
    rows = snapshots()
    for x in rows:
        x.metadata['observed_at'] = '2026-11-03T00:00:00+00:00'
    output = asyncio.run(DailySummarizer().generate_summary(list(reversed(rows)), '2026-11-03', 5, language))
    assert heading in output
    assert '2026-11-03 00:00:00 UTC' in output
    assert '/10' not in output
    assert 'No significant developments' not in output
    assert '今日暂无重要动态' not in output
    assert output.index('owner/repo1') < output.index('owner/repo5')
    assert '⭐ None' not in output


def test_ranking_text_cannot_inject_html_or_markdown():
    rows = snapshots()
    rows[0].title = 'owner/<script>alert(1)</script>'
    rows[0].content = '<script>alert(2)</script> [click](javascript:alert(1))'
    output = asyncio.run(DailySummarizer().generate_summary([], '2026-11-03', 5, 'en', trending_items=rows))
    assert '<script>' not in output
    assert '[click](javascript:' not in output


def test_native_cli_ranking_only_saves_all_five_without_a_model(tmp_path, monkeypatch):
    forbid_model(monkeypatch)
    monkeypatch.chdir(tmp_path)
    obj = HorizonOrchestrator(config(), StorageManager(str(tmp_path/'data')), console=Console(file=StringIO()))
    monkeypatch.setattr(obj, 'fetch_all_sources', AsyncMock(return_value=snapshots()))
    asyncio.run(obj.run(force_hours=24))
    summaries = list((tmp_path/'data/summaries').glob('horizon-*.md'))
    assert len(summaries) == 2
    for path in summaries:
        output = path.read_text()
        assert '[owner/repo1](https://github.com/owner/repo1)' in output
        assert '[owner/repo5](https://github.com/owner/repo5)' in output


def test_mcp_full_ranking_only_pipeline_uses_raw_snapshot_without_a_model(tmp_path, monkeypatch):
    forbid_model(monkeypatch)
    cfg = config()
    path = tmp_path/'config.json'
    path.write_text(cfg.model_dump_json())
    monkeypatch.setattr(HorizonOrchestrator, 'fetch_all_sources', AsyncMock(return_value=snapshots()))
    service = HorizonPipelineService(runs_root=tmp_path/'runs')
    result = asyncio.run(service.run_pipeline(horizon_path=str(ROOT), config_path=str(path)))
    run_id = result['run_id']
    assert len(service.run_store.load_items(run_id, 'raw')) == 5
    assert service.run_store.load_items(run_id, 'scored') == []
    assert service.run_store.load_items(run_id, 'filtered') == []
    for lang in ['en', 'zh']:
        output = (service.run_store.run_dir(run_id)/f'summary-{lang}.md').read_text()
        assert '[owner/repo5](https://github.com/owner/repo5)' in output


def test_news_quota_and_score_order_do_not_truncate_or_reorder_top_five(tmp_path):
    obj = HorizonOrchestrator(config(), StorageManager(str(tmp_path/'data')), console=Console(file=StringIO()))
    ordinary = [news('low', 6), news('top', 9), news('second', 8)]
    selected = asyncio.run(obj.select_digest_items(ordinary, threshold=7, topic_dedup=False, log=False)).items
    assert [x.id for x in selected] == ['top']
    output = asyncio.run(DailySummarizer().generate_summary(selected, '2026-11-03', 8, 'en', trending_items=snapshots()))
    assert 'Verified news summary.' in output
    assert output.count('https://github.com/owner/repo') == 5
    assert output.index('owner/repo1') < output.index('owner/repo5')


def test_mcp_summary_restores_raw_ranking_after_news_was_filtered(tmp_path, monkeypatch):
    forbid_model(monkeypatch)
    path = tmp_path/'config.json'
    path.write_text(config().model_dump_json())
    service = HorizonPipelineService(runs_root=tmp_path/'runs')
    run_id = service.run_store.create_run()
    rows = snapshots()
    selected = news('selected')
    service.run_store.save_items(run_id, 'raw', [x.model_dump(mode='json') for x in rows + [selected]])
    service.run_store.save_items(run_id, 'filtered', [selected.model_dump(mode='json')])
    asyncio.run(service.generate_summary(run_id, language='en', horizon_path=str(ROOT), config_path=str(path)))
    output = (service.run_store.run_dir(run_id)/'summary-en.md').read_text()
    assert 'Verified news summary.' in output
    assert output.count('https://github.com/owner/repo') == 5
