"""Unit tests for the WeChat (iLink Bot) notification service."""

import asyncio
import base64
import json
import os
import sys
from datetime import datetime, timezone

import httpx
import pytest
from pydantic import ValidationError

from src.ai.summarizer import DailySummarizer
from src.models import (
    ClassificationResult,
    ContentAnalysis,
    ContentItem,
    ProcessingResult,
    SourceType,
    WeChatConfig,
)
from src.services import wechat
from src.services.wechat import (
    CONTEXT_MESSAGE_BUDGET,
    ILINK_BASE_URL,
    STYLES,
    Briefing,
    Command,
    ILinkClient,
    ILinkError,
    WeChatDeliveryStatus,
    WeChatNotifier,
    WeChatSession,
    _client_version_number,
    _random_wechat_uin,
    budget_footer,
    format_markdown_for_wechat,
    help_text,
    pack_chunks,
    parse_command,
    split_text_chunks,
    style_menu,
    welcome_text,
)
from src.storage.manager import StorageManager


def _run(coro):
    return asyncio.run(coro)


def _session(**overrides) -> WeChatSession:
    data = {
        "bot_token": "bot-token-123456",
        "base_url": ILINK_BASE_URL,
        "bot_id": "bot@im.bot",
        "user_id": "user@im.wechat",
        "context_token": "ctx-1",
        "get_updates_buf": "buf-1",
    }
    data.update(overrides)
    return WeChatSession(**data)


def _item(item_id: str, score: float, title: str) -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=SourceType.HACKERNEWS,
        title=title,
        url=f"https://example.com/{item_id}",
        content="body",
        author="tester",
        published_at=datetime(2026, 4, 24, 8, 0, tzinfo=timezone.utc),
        fetched_at=datetime(2026, 4, 24, 12, 0, tzinfo=timezone.utc),
        profile="tech-news",
        processing=ProcessingResult(
            classification=ClassificationResult(profile="tech-news", method="source_override"),
            analysis=ContentAnalysis(score=score, reason="r", summary=f"{title} summary", tags=["t"]),
            artifacts={},
        ),
    )


def _message(text, token="ctx-2"):
    return {
        "message_type": 1,
        "from_user_id": "user@im.wechat",
        "context_token": token,
        "item_list": [{"type": 1, "text_item": {"text": text}}],
    }


# ── protocol helpers ──


def test_client_version_encodes_major_minor_patch():
    assert _client_version_number("2.4.9") == (2 << 16) | (4 << 8) | 9
    assert _client_version_number("1.0.11") == 0x0001000B
    assert _client_version_number("weird") == 0


def test_random_uin_is_base64_of_uint32_decimal():
    decoded = base64.b64decode(_random_wechat_uin()).decode("ascii")
    assert decoded.isdigit() and 0 <= int(decoded) <= 0xFFFFFFFF


def test_ilink_error_classification_and_hints():
    timed_out = ILinkError("x", errcode=-14)
    assert timed_out.session_timeout and "login --force" in timed_out.hint()
    exhausted = ILinkError("x", ret=-2)
    assert exhausted.budget_exhausted and "reply budget" in exhausted.hint()
    other = ILinkError("boom", ret=-5)
    assert not other.session_timeout and not other.budget_exhausted and "boom" in other.hint()


# ── session persistence ──


def test_session_roundtrip_ignores_unknown_fields(tmp_path):
    path = tmp_path / "wechat_session.json"
    _session(style="overview", context_sends=3).save(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["future_field"] = "ignored"
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = WeChatSession.load(path)
    assert loaded.bot_token == "bot-token-123456"
    assert loaded.style == "overview" and loaded.context_sends == 3
    assert loaded.ready and loaded.remaining_budget == CONTEXT_MESSAGE_BUDGET - 3


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
def test_session_file_is_owner_private(tmp_path):
    path = tmp_path / "wechat_session.json"
    _session().save(path)
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"


def test_session_load_missing_or_invalid(tmp_path):
    assert WeChatSession.load(tmp_path / "nope.json") is None
    path = tmp_path / "wechat_session.json"
    path.write_text(json.dumps({"user_id": "u"}), encoding="utf-8")
    with pytest.raises(ValueError):
        WeChatSession.load(path)


def test_session_update_from_message_adopts_user_token_and_resets_budget():
    session = _session(context_token="", context_sends=7)
    assert not session.ready
    assert not session.update_from_message({"message_type": 2, "from_user_id": "user@im.wechat", "context_token": "bot"})
    assert not session.update_from_message({"message_type": 1, "from_user_id": "other@im.wechat", "context_token": "o"})
    assert session.update_from_message({"message_type": 1, "from_user_id": "user@im.wechat", "context_token": "ctx-new"})
    assert session.context_token == "ctx-new" and session.context_sends == 0
    assert session.context_updated_at and session.ready

    unknown = _session(user_id="", context_token="")
    assert unknown.update_from_message({"message_type": 1, "from_user_id": "scanner@im.wechat", "context_token": "c"})
    assert unknown.user_id == "scanner@im.wechat"


def test_effective_style_precedence():
    config = WeChatConfig(style="summary")
    assert _session().effective_style(config).name == "summary"
    assert _session(style="overview").effective_style(config).name == "overview"
    assert _session(style="overview").effective_style(config, "summary").name == "summary"
    assert _session(style="bogus").effective_style(config).name == "summary"


# ── config ──


def test_wechat_config_defaults_and_validation():
    cfg = WeChatConfig()
    assert cfg.enabled is False and cfg.style == "summary" and cfg.chunk_size == 4000
    with pytest.raises(ValidationError):
        WeChatConfig(style="fancy")
    with pytest.raises(ValidationError):
        WeChatConfig(chunk_size=5000)


# ── chat commands ──


def test_parse_command_words_and_choices():
    assert list(STYLES) == ["summary", "overview"]  # 1 = summary (default), 2 = overview
    assert parse_command("日报") == (Command.NEWS, None)
    assert parse_command(" /news ") == (Command.NEWS, None)
    assert parse_command("帮助") == (Command.HELP, None)
    assert parse_command("?") == (Command.HELP, None)
    assert parse_command("样式") == (Command.MENU, None)
    assert parse_command("/style") == (Command.MENU, None)
    assert parse_command("s") == (Command.MENU, None)
    assert parse_command("切换") == (Command.TOGGLE_STYLE, None)
    assert parse_command("1") == (Command.SET_STYLE, "summary")
    assert parse_command(" 2") == (Command.SET_STYLE, "overview")
    assert parse_command("总览") == (Command.SET_STYLE, "overview")
    assert parse_command("/STYLE Overview") == (Command.SET_STYLE, "overview")
    assert parse_command("/样式 2") == (Command.SET_STYLE, "overview")
    assert parse_command("/style nope") == (Command.MENU, None)
    # ordinary chat stays silent
    for text in ("hi", "3", "你好", "stylish outfit", "hello there", "", "newsletter"):
        assert parse_command(text) is None, text


def test_texts_mention_commands_and_budget():
    menu = style_menu("summary", "zh", remaining=7)
    assert "`summary`" in menu and menu.count("✅") == 1 and "**1** 或 **2**" in menu and "7/10" in menu
    assert "Reply **1** or **2**" in style_menu("overview", "en")
    zh = help_text("summary", 4, "zh")
    assert "`summary`" in zh and "日报" in zh and "4/10" in zh
    en = help_text("overview", 9, "en")
    assert "Current style: `overview`" in en and "`news`" in en and "9/10" in en
    for lang in ("zh", "en"):
        assert "1 / 2" in welcome_text(lang) and "10" in welcome_text(lang)
    assert "回复任意内容" in budget_footer(1, "zh") and "1/10" in budget_footer(1, "zh")
    assert "reply with anything" in budget_footer(0, "en")


# ── text formatting ──


def test_format_markdown_cleans_wechat_unfriendly_constructs():
    text = (
        "# Title\n\n![alt](https://img.example/x.png)\n\n##### Deep\n\n"
        "1. [GPT-5](#item-1) · [site](https://example.com/x)\n\n"
        "看 *中文强调* 和 *emphasis* 与 _下划线_ 和 _under_ **bold**\n\n"
        '<details><summary>Refs</summary><ul><li><a href="https://example.com/a">Link A</a></li></ul></details>'
    )
    result = format_markdown_for_wechat(text)
    assert "![" not in result and "#####" not in result and "Deep" in result
    assert "(#item" not in result and "GPT-5" in result and "[site](https://example.com/x)" in result
    assert "*中文强调*" not in result and "中文强调" in result and "*emphasis*" in result
    assert "_下划线_" not in result and "_under_" in result and "**bold**" in result
    assert "<details>" not in result and "[Link A](https://example.com/a)" in result


def test_split_text_chunks_prefers_paragraph_boundaries_then_hard_splits():
    paragraphs = [f"para {i} " + "x" * 40 for i in range(10)]
    chunks = split_text_chunks("\n\n".join(paragraphs), limit=120)
    assert len(chunks) > 1 and all(len(c) <= 120 and c.startswith("para") for c in chunks)
    assert split_text_chunks("a" * 250, limit=100) == ["a" * 100, "a" * 100, "a" * 50]
    assert split_text_chunks("   ", limit=10) == [] and split_text_chunks("short", limit=10) == ["short"]
    with pytest.raises(ValueError):
        split_text_chunks("x", limit=0)


def test_pack_chunks_merges_bodies_only_when_over_budget():
    bodies = ["a" * 30, "b" * 30, "c" * 30]
    assert pack_chunks(bodies, limit=100, max_messages=3) == bodies
    packed = pack_chunks(bodies, limit=100, max_messages=2)
    assert packed == ["a" * 30 + "\n\n---\n\n" + "b" * 30, "c" * 30]
    assert all(len(c) <= 100 for c in pack_chunks(bodies, limit=100, max_messages=1))
    assert pack_chunks(["x" * 250], limit=100, max_messages=1) == ["x" * 100] * 2 + ["x" * 50]


# ── HTTP client ──


class FakeTransport:
    """Records requests made through safe_request and returns canned responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def __call__(self, client, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        status, body = response
        return httpx.Response(status, json=body, request=httpx.Request(method, url))


def test_send_text_builds_ilink_request(monkeypatch):
    transport = FakeTransport([(200, {"ret": 0, "message_id": 42})])
    monkeypatch.setattr(wechat, "safe_request", transport)

    data = _run(ILinkClient("https://api.example/", "tok").send_text("user@im.wechat", "hello", context_token="ctx"))
    assert data["ret"] == 0

    call = transport.calls[0]
    assert call["method"] == "POST" and call["url"] == "https://api.example/ilink/bot/sendmessage"
    headers = call["headers"]
    assert headers["Authorization"] == "Bearer tok"
    assert headers["AuthorizationType"] == "ilink_bot_token"
    assert headers["iLink-App-Id"] == "bot" and headers["Content-Type"] == "application/json"
    assert base64.b64decode(headers["X-WECHAT-UIN"]).decode().isdigit()

    body = json.loads(call["content"])
    assert body["base_info"]["channel_version"] and body["base_info"]["bot_agent"].startswith("Horizon/")
    msg = body["msg"]
    assert msg["to_user_id"] == "user@im.wechat" and msg["message_type"] == 2 and msg["message_state"] == 2
    assert msg["context_token"] == "ctx" and msg["client_id"].startswith("horizon:")
    assert msg["item_list"] == [{"type": 1, "text_item": {"text": "hello"}}]


def test_client_surfaces_business_and_http_errors(monkeypatch):
    transport = FakeTransport([(200, {"ret": -2, "errmsg": "prepare failed"}), (500, {"error": "boom"})])
    monkeypatch.setattr(wechat, "safe_request", transport)
    client = ILinkClient(bot_token="tok")
    with pytest.raises(ILinkError) as excinfo:
        _run(client.send_text("u", "hi", context_token="ctx"))
    assert excinfo.value.budget_exhausted
    with pytest.raises(ILinkError) as excinfo:
        _run(client.send_text("u", "hi", context_token="ctx"))
    assert "HTTP 500" in str(excinfo.value)


def test_get_updates_timeout_and_errcode(monkeypatch):
    transport = FakeTransport([httpx.ReadTimeout("slow"), (200, {"ret": 0, "errcode": -14, "errmsg": "stale"})])
    monkeypatch.setattr(wechat, "safe_request", transport)
    client = ILinkClient(bot_token="tok")
    assert _run(client.get_updates("buf-1", timeout=1.0)) == {"ret": 0, "msgs": [], "get_updates_buf": "buf-1"}
    assert json.loads(transport.calls[0]["content"])["get_updates_buf"] == "buf-1"
    with pytest.raises(ILinkError) as excinfo:
        _run(client.get_updates(""))
    assert excinfo.value.session_timeout


def test_qrcode_endpoints(monkeypatch):
    transport = FakeTransport(
        [(200, {"qrcode": "q1", "qrcode_img_content": "https://qr.example/q1"}), (200, {"status": "wait"})]
    )
    monkeypatch.setattr(wechat, "safe_request", transport)
    client = ILinkClient()

    assert _run(client.get_bot_qrcode(["old-token"]))["qrcode"] == "q1"
    first = transport.calls[0]
    assert first["url"] == f"{ILINK_BASE_URL}/ilink/bot/get_bot_qrcode?bot_type=3"
    assert "Authorization" not in first["headers"]
    assert json.loads(first["content"]) == {"local_token_list": ["old-token"]}

    assert _run(client.get_qrcode_status("q 1", verify_code="12 34", base_url="https://sh.example")) == {"status": "wait"}
    second = transport.calls[1]
    assert second["method"] == "GET" and second["url"].startswith("https://sh.example/ilink/bot/get_qrcode_status?")
    assert "qrcode=q+1" in second["url"] or "qrcode=q%201" in second["url"]
    assert "verify_code=12" in second["url"] and "Content-Type" not in second["headers"]


# ── notifier ──


class FakeClient:
    def __init__(self, *, updates=None, send_error=None, fail_after=None):
        self.updates = updates or {"ret": 0, "msgs": [], "get_updates_buf": ""}
        self.send_error = send_error
        self.fail_after = fail_after  # raise ret=-2 once this many sends succeeded
        self.sent = []

    async def get_updates(self, buf, *, timeout):
        if isinstance(self.updates, Exception):
            raise self.updates
        return self.updates

    async def send_text(self, to_user_id, text, *, context_token):
        if self.send_error:
            raise self.send_error
        if self.fail_after is not None and len(self.sent) >= self.fail_after:
            raise ILinkError("sendmessage failed: ret=-2 errmsg=prepare failed", ret=-2)
        self.sent.append({"to": to_user_id, "text": text, "context_token": context_token})
        return {"ret": 0}


def _notifier(tmp_path, monkeypatch, *, session=None, fake=None, **config_overrides):
    config = WeChatConfig(enabled=True, **config_overrides)
    storage = StorageManager(data_dir=str(tmp_path))
    if session is not None:
        session.save(tmp_path / "wechat_session.json")
    notifier = WeChatNotifier(config, storage)
    fake = fake or FakeClient()
    monkeypatch.setattr(notifier, "client", lambda: fake)
    return notifier, fake


def _deliver(notifier, items, *, summary="unused", lang="en", all_items_count=None, **kwargs):
    return _run(
        notifier.send_daily_summary(
            summary=summary,
            important_items=items,
            all_items_count=len(items) if all_items_count is None else all_items_count,
            date="2026-04-24",
            lang=lang,
            summarizer=DailySummarizer(),
            **kwargs,
        )
    )


def _saved(tmp_path):
    return json.loads((tmp_path / "wechat_session.json").read_text(encoding="utf-8"))


def test_default_summary_style_sends_whole_briefing_in_chunks(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), chunk_size=400)
    items = [_item(f"hn:{i}", 8.0, f"Story {i}") for i in range(3)]
    summary = _run(DailySummarizer().generate_summary(items, "2026-04-24", 3, language="en"))

    result = _deliver(notifier, items, summary=summary)

    assert result.status == WeChatDeliveryStatus.SUCCESS
    assert result.chunks_sent == len(fake.sent) > 1
    assert all(len(call["text"]) <= 400 for call in fake.sent)
    assert all(call["to"] == "user@im.wechat" and call["context_token"] == "ctx-1" for call in fake.sent)
    assert "Story 0" in fake.sent[0]["text"]
    assert _saved(tmp_path)["context_sends"] == len(fake.sent)


def test_overview_style_sends_overview_then_full_items(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), style="overview")
    items = [_item("hn:1", 9.0, "Alpha"), _item("hn:2", 7.0, "Beta")]

    result = _deliver(notifier, items, all_items_count=5)

    assert result.status == WeChatDeliveryStatus.SUCCESS and result.chunks_sent == 3
    overview, first, second = (call["text"] for call in fake.sent)
    assert "Selected 2 important items" in overview and "[Alpha](https://example.com/hn:1)" in overview
    assert first.startswith("Item 1/2\n\n## [Alpha](https://example.com/hn:1) ⭐️ 9.0/10")
    assert first.count("Item 1/2") == 1 and "**Tags**" in first
    assert second.startswith("Item 2/2") and "⚠️" not in second


def test_style_override_beats_chat_choice_and_config(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(style="overview"))
    result = _deliver(notifier, [_item("hn:1", 9.0, "Alpha")], summary="# whole", style="summary")
    assert result.chunks_sent == 1 and fake.sent[0]["text"] == "# whole"
    assert _saved(tmp_path)["style"] == "overview"  # the chat choice is untouched


def test_overview_style_packs_items_when_budget_is_short(tmp_path, monkeypatch):
    notifier, fake = _notifier(
        tmp_path, monkeypatch, session=_session(context_sends=CONTEXT_MESSAGE_BUDGET - 2), style="overview"
    )
    items = [_item(f"hn:{i}", 8.0, f"Story {i}") for i in range(5)]

    result = _deliver(notifier, items)

    assert result.status == WeChatDeliveryStatus.SUCCESS
    assert 1 <= result.chunks_sent == len(fake.sent) <= 2  # 6 bodies fitted into 2 replies
    assert "Story 0" in fake.sent[0]["text"] and "Story 4" in fake.sent[-1]["text"]
    assert "reply with anything" in fake.sent[-1]["text"]


def test_low_budget_adds_footer_only_to_last_message(tmp_path, monkeypatch):
    notifier, fake = _notifier(
        tmp_path, monkeypatch, session=_session(context_sends=CONTEXT_MESSAGE_BUDGET - 3), style="overview"
    )
    result = _deliver(notifier, [_item("hn:1", 9.0, "Alpha")], lang="zh")
    assert result.chunks_sent == 2
    assert "回复任意内容" not in fake.sent[0]["text"]
    assert "回复任意内容" in fake.sent[1]["text"] and "1/10" in fake.sent[1]["text"]


def test_budget_exhausted_reports_hint_and_syncs_counter(tmp_path, monkeypatch, capsys):
    notifier, _ = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(fail_after=1), style="overview")
    result = _deliver(notifier, [_item("hn:1", 9.0, "Alpha"), _item("hn:2", 7.0, "Beta")])
    assert result.status == WeChatDeliveryStatus.PLATFORM_FAILURE and result.chunks_sent == 1
    assert "reply budget" in capsys.readouterr().err
    assert _saved(tmp_path)["context_sends"] == CONTEXT_MESSAGE_BUDGET


def test_new_user_message_resets_budget_and_refreshes_token(tmp_path, monkeypatch):
    updates = {"ret": 0, "get_updates_buf": "buf-2", "msgs": [{"message_type": 1, "from_user_id": "user@im.wechat", "context_token": "ctx-2"}]}
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(context_sends=9), fake=FakeClient(updates=updates))

    result = _run(notifier.send_failure("2026-04-24", "boom"))

    assert result.status == WeChatDeliveryStatus.SUCCESS and fake.sent[0]["context_token"] == "ctx-2"
    saved = _saved(tmp_path)
    assert saved["context_token"] == "ctx-2" and saved["get_updates_buf"] == "buf-2" and saved["context_sends"] == 1


def test_inbox_is_polled_once_per_run(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session())
    polls = {"n": 0}
    real = fake.get_updates

    async def counting(buf, *, timeout):
        polls["n"] += 1
        return await real(buf, timeout=timeout)

    fake.get_updates = counting
    _deliver(notifier, [], summary="zh", lang="en", all_items_count=0)
    _deliver(notifier, [], summary="en", lang="en", all_items_count=0)
    assert polls["n"] == 1


def test_bare_digit_switches_style_and_replies(tmp_path, monkeypatch):
    updates = {"ret": 0, "get_updates_buf": "buf-2", "msgs": [_message("2")]}
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(updates=updates))

    assert _run(notifier.refresh_context()) is True
    assert notifier.style().name == "overview"
    assert fake.sent[0]["context_token"] == "ctx-2" and "`overview`" in fake.sent[0]["text"]
    saved = _saved(tmp_path)
    assert saved["style"] == "overview" and saved["context_sends"] == 1

    fake.sent.clear()
    fake.updates = {"ret": 0, "msgs": [], "get_updates_buf": "buf-2"}
    _deliver(notifier, [_item("hn:1", 9.0, "Alpha")])
    assert len(fake.sent) == 2 and "Selected 1 important" in fake.sent[0]["text"]


def test_toggle_command_flips_between_styles(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(updates={"ret": 0, "msgs": [_message("切换", "ctx-6")]}))
    _run(notifier.refresh_context())
    assert notifier.style().name == "overview" and "`overview`" in fake.sent[0]["text"]
    fake.updates = {"ret": 0, "msgs": [_message("切换", "ctx-7")]}
    _run(notifier.refresh_context())
    assert notifier.style().name == "summary"


def test_menu_and_help_commands_reply(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(updates={"ret": 0, "msgs": [_message("样式", "ctx-3")]}), languages=["en"])
    _run(notifier.refresh_context())
    assert notifier.style().name == "summary"
    assert "Horizon message styles" in fake.sent[0]["text"] and f"9/{CONTEXT_MESSAGE_BUDGET} pushes left" in fake.sent[0]["text"]

    fake.updates = {"ret": 0, "msgs": [_message("/help", "ctx-5")]}
    _run(notifier.refresh_context())
    assert "Horizon WeChat delivery" in fake.sent[1]["text"] and "`news`" in fake.sent[1]["text"]


def test_news_command_replays_last_briefing_in_current_style(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), languages=["en"])
    items = [_item("hn:1", 9.0, "Alpha"), _item("hn:2", 7.0, "Beta")]
    summary = _run(DailySummarizer().generate_summary(items, "2026-04-24", 2, language="en"))

    _deliver(notifier, items, summary=summary)  # caches both layouts
    cached = Briefing.load(tmp_path, "en")
    assert cached.date == "2026-04-24" and cached.summary == summary and len(cached.items) == 2
    fake.sent.clear()

    fake.updates = {"ret": 0, "msgs": [_message("news", "ctx-10")]}
    _run(notifier.refresh_context())
    assert len(fake.sent) == 1 and fake.sent[0]["text"].startswith("# Horizon Daily - 2026-04-24")
    fake.sent.clear()

    notifier.session.style = "overview"
    fake.updates = {"ret": 0, "msgs": [_message("news", "ctx-11")]}
    _run(notifier.refresh_context())
    assert len(fake.sent) == 3
    assert "Selected 2 important" in fake.sent[0]["text"]
    assert fake.sent[1]["text"].startswith("Item 1/2\n\n## [Alpha]") and fake.sent[1]["text"].count("Item 1/2") == 1
    assert fake.sent[2]["text"].startswith("Item 2/2")


def test_news_command_falls_back_to_saved_summary_then_explains(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(updates={"ret": 0, "msgs": [_message("日报", "ctx-8")]}))
    _run(notifier.refresh_context())
    assert "还没有生成过日报" in fake.sent[0]["text"]

    notifier.storage.save_daily_summary("2026-04-23", "# 旧的一期", language="zh")
    notifier.storage.save_daily_summary("2026-04-24", "# 最新一期\n\n内容", language="zh")
    notifier.storage.save_daily_summary("2026-04-25", "# English only", language="en")
    assert notifier.storage.latest_daily_summary("zh") == ("2026-04-24", "# 最新一期\n\n内容")
    assert notifier.storage.latest_daily_summary("ja") is None
    fake.updates = {"ret": 0, "msgs": [_message("日报", "ctx-9")]}
    _run(notifier.refresh_context())
    assert fake.sent[1]["text"].startswith("# 最新一期")


def test_sample_sends_do_not_replace_the_replay_cache(tmp_path, monkeypatch):
    notifier, _ = _notifier(tmp_path, monkeypatch, session=_session())
    _deliver(notifier, [_item("hn:1", 9.0, "Alpha")], summary="sample", remember=False)
    assert Briefing.load(tmp_path, "en") is None


def test_non_command_messages_do_not_trigger_replies(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(updates={"ret": 0, "msgs": [_message("hello there", "ctx-4")]}))
    _run(notifier.refresh_context())
    assert fake.sent == [] and notifier.session.context_token == "ctx-4" and notifier.session.context_sends == 0


def test_delivery_reloads_session_updated_by_another_process(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session())
    _session(context_token="ctx-listen", style="overview", context_sends=3).save(tmp_path / "wechat_session.json")

    result = _deliver(notifier, [_item("hn:1", 9.0, "Alpha")])

    assert result.status == WeChatDeliveryStatus.SUCCESS and len(fake.sent) == 2
    assert all(call["context_token"] == "ctx-listen" for call in fake.sent)
    assert _saved(tmp_path)["context_sends"] == 5


def test_delivery_proceeds_when_inbox_session_timed_out(tmp_path, monkeypatch, capsys):
    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(updates=ILinkError("getupdates failed", errcode=-14)))
    result = _deliver(notifier, [_item("hn:1", 9.0, "Alpha")], summary="# briefing")
    assert result.status == WeChatDeliveryStatus.SUCCESS and fake.sent[0]["text"] == "# briefing"
    assert "receive session" in capsys.readouterr().err


def test_not_ready_and_disabled_outcomes(tmp_path, monkeypatch):
    notifier, fake = _notifier(tmp_path, monkeypatch)
    assert notifier.session is None
    assert _run(notifier.send_text("hello")).status == WeChatDeliveryStatus.SKIPPED
    assert _deliver(notifier, []).status == WeChatDeliveryStatus.SKIPPED

    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(context_token=""))
    result = _run(notifier.send_text("hello"))
    assert result.status == WeChatDeliveryStatus.SKIPPED and "context token" in result.detail

    notifier, fake = _notifier(tmp_path, monkeypatch, session=_session(), languages=["zh"])
    assert _deliver(notifier, [], summary="x", all_items_count=0).status == WeChatDeliveryStatus.SKIPPED
    assert fake.sent == []

    config = WeChatConfig(enabled=False)
    _session().save(tmp_path / "wechat_session.json")
    disabled = WeChatNotifier(config, StorageManager(data_dir=str(tmp_path)))
    assert _run(disabled.send_text("x")).status == WeChatDeliveryStatus.DISABLED


def test_failures_are_reported_as_results(tmp_path, monkeypatch, capsys):
    notifier, _ = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(send_error=ILinkError("nope", ret=-5)))
    assert _run(notifier.send_text("hello")).status == WeChatDeliveryStatus.PLATFORM_FAILURE

    notifier, _ = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(send_error=ILinkError("x", errcode=-14)))
    result = _run(notifier.send_text("hello"))
    assert result.status == WeChatDeliveryStatus.PLATFORM_FAILURE and "login --force" in capsys.readouterr().err

    notifier, _ = _notifier(tmp_path, monkeypatch, session=_session(), fake=FakeClient(send_error=httpx.ConnectError("down")))
    assert _run(notifier.send_text("hello")).status == WeChatDeliveryStatus.NETWORK_FAILURE
