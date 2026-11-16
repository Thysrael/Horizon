"""Score arbitrary article URLs without publishing a digest."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from src import main as main_module
from src.ai.summarizer import DailySummarizer
from src.extractors.trafilatura import ExtractedArticle, TrafilaturaExtractor
from src.mcp.errors import HorizonMcpError
from src.mcp.server import hz_score_urls
from src.mcp.service import HorizonPipelineService
from src.orchestrator import HorizonOrchestrator
from src.storage.manager import StorageManager


ROOT = Path(__file__).resolve().parents[1]
GOOD_URL = "https://example.com/essay"
BAD_URL = "https://example.com/missing"
READING_RUBRIC = "Score durable reading value"


class FakeAIClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def complete(self, system: str, user: str, temperature: float | None = None, max_tokens: int | None = None) -> str:
        self.calls.append({"system": system, "user": user})
        return json.dumps(
            {
                "score": 8.5,
                "reason": "Durable insight worth rereading.",
                "summary": "An essay with a transferable idea.",
                "tags": ["essay"],
            }
        )


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "config.json"
    path.write_text((ROOT / "data" / "config.example.json").read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _service(tmp_path: Path) -> HorizonPipelineService:
    return HorizonPipelineService(runs_root=tmp_path / "mcp-runs")


def _forbid_digest_publication(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def boom(name: str, *, sync: bool = False):
        def rejected(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"{name} must not run during URL scoring")

        async def rejected_async(*args, **kwargs):
            rejected(*args, **kwargs)

        return rejected if sync else rejected_async

    monkeypatch.setattr(HorizonOrchestrator, "enrich_items", boom("enrich_items"))
    monkeypatch.setattr(HorizonOrchestrator, "select_digest_items", boom("select_digest_items"))
    monkeypatch.setattr(HorizonPipelineService, "filter_items", boom("filter_items"))
    monkeypatch.setattr(HorizonPipelineService, "enrich_items", boom("service.enrich_items"))
    monkeypatch.setattr(HorizonPipelineService, "generate_summary", boom("generate_summary"))
    monkeypatch.setattr(HorizonPipelineService, "run_pipeline", boom("run_pipeline"))
    monkeypatch.setattr(DailySummarizer, "generate_summary", boom("DailySummarizer.generate_summary"))
    monkeypatch.setattr(StorageManager, "save_daily_summary", boom("save_daily_summary", sync=True))
    return calls


def _patch_fetch_and_model(monkeypatch: pytest.MonkeyPatch, client: FakeAIClient) -> list[str]:
    fetched: list[str] = []

    async def extract_article(self, url: str, http_client) -> ExtractedArticle:
        fetched.append(url)
        if url == BAD_URL:
            return ExtractedArticle(error="HTTPStatusError: 404")
        return ExtractedArticle(content=f"Full text of {url}", title="Known Title")

    monkeypatch.setattr(TrafilaturaExtractor, "extract_article", extract_article)
    monkeypatch.setattr("src.orchestrator.create_ai_client", lambda config: client)
    monkeypatch.setattr("src.mcp.horizon_adapter.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.mcp.horizon_adapter._load_mcp_secrets", lambda *args, **kwargs: None)
    return fetched


def _assert_unpublished(tmp_path: Path, service: HorizonPipelineService, run_id: str, calls: list[str]) -> None:
    assert calls == []
    run_dir = service.run_store.run_dir(run_id)
    assert list(run_dir.glob("summary-*.md")) == []
    assert list((tmp_path / "summaries").glob("*.md")) == []
    assert not service.run_store.has_stage(run_id, "filtered")
    assert not service.run_store.has_stage(run_id, "enriched")


def test_score_urls_maps_analyzer_output_for_default_reading_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeAIClient()
    calls = _forbid_digest_publication(monkeypatch)
    fetched = _patch_fetch_and_model(monkeypatch, client)
    service = _service(tmp_path)

    result = asyncio.run(
        service.score_urls(
            urls=[f"  {GOOD_URL}  "],
            horizon_path=str(ROOT),
            config_path=str(_config(tmp_path)),
        )
    )

    assert result["profile"] == "reading"
    assert result["scored"] == 1
    assert result["failed"] == 0
    assert result["results"] == [
        {
            "url": GOOD_URL,
            "title": "Known Title",
            "score": 8.5,
            "reason": "Durable insight worth rereading.",
            "summary": "An essay with a transferable idea.",
            "tags": ["essay"],
            "error": None,
        }
    ]
    assert fetched == [GOOD_URL]
    assert len(client.calls) == 1
    assert READING_RUBRIC in client.calls[0]["system"]
    assert "Groundbreaking" not in client.calls[0]["system"]
    assert f"Full text of {GOOD_URL}" in client.calls[0]["user"]
    stored = service.run_store.load_items(result["run_id"], "scored")
    assert stored[0]["profile"] == "reading"
    assert stored[0]["content"] == f"Full text of {GOOD_URL}"
    _assert_unpublished(tmp_path, service, result["run_id"], calls)


def test_score_urls_reports_fetch_failure_without_aborting_the_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeAIClient()
    calls = _forbid_digest_publication(monkeypatch)
    _patch_fetch_and_model(monkeypatch, client)
    service = _service(tmp_path)

    result = asyncio.run(
        service.score_urls(
            urls=[BAD_URL, GOOD_URL],
            horizon_path=str(ROOT),
            config_path=str(_config(tmp_path)),
        )
    )

    assert [item["url"] for item in result["results"]] == [BAD_URL, GOOD_URL]
    assert result["results"][0]["score"] is None
    assert result["results"][0]["error"] == "HTTPStatusError: 404"
    assert result["results"][0]["title"] is None
    assert result["results"][1]["score"] == 8.5
    assert result["results"][1]["error"] is None
    assert result["failed"] == 1
    assert result["scored"] == 1
    assert len(client.calls) == 1
    assert BAD_URL not in client.calls[0]["user"]
    assert result["profile"] == "reading"
    stored = service.run_store.load_items(result["run_id"], "scored")
    assert [item["url"] for item in stored] == [GOOD_URL]
    _assert_unpublished(tmp_path, service, result["run_id"], calls)


def test_score_urls_reports_analysis_failure_without_aborting_the_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _forbid_digest_publication(monkeypatch)
    bad_url = "https://example.com/bad-article"
    good_url = "https://example.com/good-article"

    async def extract_article(self, url: str, http_client) -> ExtractedArticle:
        if url == bad_url:
            return ExtractedArticle(content="bad-article body", title="Broken Page")
        return ExtractedArticle(content="good article body", title="Known Title")

    class ScriptedClient:
        async def complete(
            self,
            system: str,
            user: str,
            temperature: float | None = None,
            max_tokens: int | None = None,
        ) -> str:
            if "bad-article" in user:
                return "not json"
            return json.dumps(
                {
                    "score": 6,
                    "reason": "Useful but narrow.",
                    "summary": "A narrower piece.",
                    "tags": ["notes"],
                }
            )

    monkeypatch.setattr(TrafilaturaExtractor, "extract_article", extract_article)
    monkeypatch.setattr("src.orchestrator.create_ai_client", lambda config: ScriptedClient())
    monkeypatch.setattr("src.mcp.horizon_adapter.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.mcp.horizon_adapter._load_mcp_secrets", lambda *args, **kwargs: None)
    service = _service(tmp_path)

    result = asyncio.run(
        service.score_urls(
            urls=[bad_url, good_url],
            horizon_path=str(ROOT),
            config_path=str(_config(tmp_path)),
        )
    )

    assert result["profile"] == "reading"
    assert result["results"][0]["url"] == bad_url
    assert result["results"][0]["title"] == "Broken Page"
    assert result["results"][0]["score"] is None
    assert result["results"][0]["error"] == "Analysis response parse failed"
    assert result["results"][0]["summary"] == "Broken Page"
    assert result["results"][1]["score"] == 6
    assert result["results"][1]["error"] is None
    assert result["failed"] == 1
    assert result["scored"] == 1
    _assert_unpublished(tmp_path, service, result["run_id"], calls)


def test_score_urls_rejects_an_unknown_profile_before_fetch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fetched: list[str] = []

    async def extract_article(self, url: str, http_client) -> ExtractedArticle:
        fetched.append(url)
        return ExtractedArticle(content="unused", title="unused")

    monkeypatch.setattr(TrafilaturaExtractor, "extract_article", extract_article)
    monkeypatch.setattr("src.mcp.horizon_adapter.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr("src.mcp.horizon_adapter._load_mcp_secrets", lambda *args, **kwargs: None)
    service = _service(tmp_path)

    with pytest.raises(HorizonMcpError) as exc_info:
        asyncio.run(
            service.score_urls(
                urls=[GOOD_URL],
                profile="missing-profile",
                horizon_path=str(ROOT),
                config_path=str(_config(tmp_path)),
            )
        )

    assert exc_info.value.code == "HZ_INVALID_INPUT"
    assert fetched == []


def test_hz_score_urls_delegates_to_the_service(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    async def score_urls(self, urls, profile="reading", horizon_path=None, config_path=None):
        seen.update(urls=urls, profile=profile, horizon_path=horizon_path, config_path=config_path)
        return {"profile": profile, "results": []}

    monkeypatch.setattr(HorizonPipelineService, "score_urls", score_urls)

    result = asyncio.run(hz_score_urls(urls=[GOOD_URL], config_path="data/reading.json"))

    assert result["ok"] is True
    assert result["tool"] == "hz_score_urls"
    assert result["data"]["profile"] == "reading"
    assert seen == {
        "urls": [GOOD_URL],
        "profile": "reading",
        "horizon_path": None,
        "config_path": "data/reading.json",
    }


def test_cli_score_prints_service_json_and_defaults_profile(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    seen: dict[str, object] = {}

    async def score_urls(self, urls, profile="reading", horizon_path=None, config_path=None):
        seen.update(urls=list(urls), profile=profile, horizon_path=horizon_path, config_path=config_path)
        return {"profile": profile, "results": [{"url": urls[0], "score": 8.5, "error": None}]}

    monkeypatch.setattr(main_module.HorizonPipelineService, "score_urls", score_urls)
    monkeypatch.setattr(main_module, "configure_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "StorageManager", lambda *args, **kwargs: pytest.fail("digest CLI must not load storage"))
    monkeypatch.setattr(
        "sys.argv",
        ["horizon", "score", "--urls", GOOD_URL, BAD_URL, "--config", "data/reading.json"],
    )

    main_module.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["profile"] == "reading"
    assert payload["results"][0]["score"] == 8.5
    assert seen["urls"] == [GOOD_URL, BAD_URL]
    assert seen["profile"] == "reading"
    assert seen["horizon_path"] is None
    assert seen["config_path"] == "data/reading.json"


def test_cli_score_reports_service_errors_as_json(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    async def score_urls(self, urls, profile="reading", horizon_path=None, config_path=None):
        raise HorizonMcpError(code="HZ_CONFIG_NOT_FOUND", message="Config file does not exist.", details=None)

    monkeypatch.setattr(main_module.HorizonPipelineService, "score_urls", score_urls)
    monkeypatch.setattr(main_module, "configure_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr("sys.argv", ["horizon", "score", "--urls", GOOD_URL, "--data-dir", "custom-data"])

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "HZ_CONFIG_NOT_FOUND"


def test_score_help_describes_the_digest_boundary(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main_module.score_main(["--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "DEEPSEEK_API_KEY" in help_text
    assert "reading" in help_text
    assert "digest" in help_text
    assert "--urls" in help_text
