"""Integration checks for the personal configuration; no model or network required."""
import asyncio
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from configs.personal.check import load_config
from src.ai.summarizer import DailySummarizer
from src.models import (ClassificationResult, ContentAnalysis, ContentArtifact,
                        ContentBlock, ContentItem, ProcessingResult, SourceType)
from src.orchestrator import HorizonOrchestrator


def test_config_loads_every_profile_and_references():
    config, profiles = load_config()
    assert len(profiles.ids) == 6
    assert set(config.digest.profile_order) == profiles.ids
    assert {s.profile for s in config.sources.rss if s.enabled} == profiles.ids
    assert config.ai.languages == ['zh']
    from src.mcp.horizon_adapter import get_enabled_sources
    assert get_enabled_sources(config) == ['rss']
    assert config.email is None
    assert not config.webhook.enabled and not config.wechat.enabled


def test_real_selection_respects_total_and_topic_caps():
    config, profiles = load_config()
    items = []
    for pid in sorted(profiles.ids):
        for index in range(10):
            items.append(ContentItem(
                id=f'{pid}-{index}', source_type=SourceType.RSS,
                title=f'{pid}-{index}', url=f'https://example.com/{pid}/{index}',
                published_at=datetime.now(timezone.utc), profile=pid,
                processing=ProcessingResult(
                    classification=ClassificationResult(profile=pid, method='source_override'),
                    analysis=ContentAnalysis(score=10-index/10, reason='test evidence', summary='test'))))
    orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
    orchestrator.config = config
    selected = orchestrator.apply_balanced_digest(items, log=False).items
    counts = Counter(i.profile for i in selected)
    assert len(selected) == 15
    assert max(counts.values()) <= 3
    assert set(counts) == profiles.ids  # With equal supply in this test, all interests are represented.


def test_chinese_digest_preserves_publisher_and_original_link():
    config, profiles = load_config()
    item = ContentItem(
        id='rss:sample', source_type=SourceType.RSS, title='Original title',
        url='https://example.com/original-article', published_at=datetime.now(timezone.utc),
        metadata={'feed_name': 'Original publisher'}, profile='world-affairs',
        processing=ProcessingResult(
            classification=ClassificationResult(profile='world-affairs', method='source_override'),
            analysis=ContentAnalysis(score=8, reason='test', summary='仅用于渲染测试'),
            artifacts={'zh': ContentArtifact(language='zh', title='中文标题', blocks=[
                ContentBlock(id='summary', title='要点', content='这是合成测试，非真实日报。', primary=True)])}))
    rendered = asyncio.run(DailySummarizer(profile_names=profiles.names,
                                         profile_order=config.digest.profile_order)
                           .generate_summary([item], '2026-11-04', 1, language='zh'))
    assert '中文标题' in rendered
    assert '国际政治与国际关系' in rendered
    assert 'Original publisher' in rendered
    assert 'https://example.com/original-article' in rendered


def test_run_rejects_missing_secret_without_starting_a_process(monkeypatch):
    import pytest
    from configs.personal import check
    monkeypatch.setenv('HORIZON_AI_MODEL', 'test-model')
    monkeypatch.setenv('HORIZON_AI_BASE_URL', 'https://api.example.com/v1')
    monkeypatch.delenv('HORIZON_AI_KEY', raising=False)
    monkeypatch.setattr(sys, 'argv', ['check.py', 'run'])
    def forbidden(*args, **kwargs):
        raise AssertionError('A missing Secret must not launch inference')
    monkeypatch.setattr(check.subprocess, 'run', forbidden)
    with pytest.raises(SystemExit) as exc:
        check.main()
    assert exc.value.code == 2


def test_run_rejects_insecure_endpoint_before_launch(monkeypatch):
    import pytest
    from configs.personal import check
    monkeypatch.setenv('HORIZON_AI_MODEL', 'test-model')
    monkeypatch.setenv('HORIZON_AI_BASE_URL', 'http://api.example.com/v1')
    monkeypatch.setenv('HORIZON_AI_KEY', 'synthetic-unit-test-only')
    monkeypatch.setattr(sys, 'argv', ['check.py', 'run'])
    def forbidden(*args, **kwargs):
        raise AssertionError('An insecure endpoint must not launch inference')
    monkeypatch.setattr(check.subprocess, 'run', forbidden)
    with pytest.raises(SystemExit) as exc:
        check.main()
    assert exc.value.code == 2
