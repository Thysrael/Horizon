import asyncio
import json
import re
from types import SimpleNamespace

import pytest

from src import _cli
from src.models import WeChatConfig
from src.services import wechat_cli
from src.services.wechat import ILINK_BASE_URL, WeChatSession
from src.storage.manager import StorageManager


def _fake_config(wechat=None, languages=("en",), icon_style="emoji"):
    return SimpleNamespace(
        wechat=wechat,
        ai=SimpleNamespace(languages=list(languages)),
        display=SimpleNamespace(icon_style=icon_style),
    )


def _silence(monkeypatch):
    monkeypatch.setattr(wechat_cli, "configure_logging", lambda console, level=None: None)
    monkeypatch.setattr(wechat_cli.console, "print", lambda *args, **kwargs: None)
    monkeypatch.setattr(wechat_cli, "load_dotenv", lambda: None)


def _capture(monkeypatch):
    """Collect console output as plain text (Rich markup stripped)."""
    printed = []

    def record(*args, **kwargs):
        text = str(args[0]) if args else ""
        printed.append(re.sub(r"\[/?[a-z ]+\]", "", text))

    monkeypatch.setattr(wechat_cli.console, "print", record)
    return printed


def _recording_storage(calls, data_dir_value, config=None):
    class RecordingStorage(StorageManager):
        def __init__(self, data_dir, config_path):
            calls.append({"data_dir": data_dir, "config_path": config_path})
            super().__init__(data_dir=str(data_dir_value))

        def load_config(self):
            return config or _fake_config()

    return RecordingStorage


def _use_storage(monkeypatch, tmp_path, config=None, calls=None):
    monkeypatch.setattr(_cli, "StorageManager", _recording_storage(calls if calls is not None else [], tmp_path, config))


def _save_session(tmp_path, **overrides):
    data = {"bot_token": "supersecret-bot-token", "user_id": "user@im.wechat", "context_token": "ctx", "bot_id": "bot@im.bot"}
    data.update(overrides)
    WeChatSession(**data).save(tmp_path / "wechat_session.json")


def test_data_dir_and_config_flags_are_forwarded(monkeypatch, tmp_path):
    calls = []
    _silence(monkeypatch)
    _use_storage(monkeypatch, tmp_path, calls=calls)
    monkeypatch.setattr("sys.argv", ["horizon-wechat", "-d", str(tmp_path), "-c", str(tmp_path / "h.json"), "status"])

    with pytest.raises(SystemExit) as excinfo:
        wechat_cli.main()

    assert excinfo.value.code == 1  # no session file yet
    assert calls == [{"data_dir": str(tmp_path), "config_path": str(tmp_path / "h.json")}]


def test_status_reports_saved_session_with_redacted_token(monkeypatch, tmp_path):
    _silence(monkeypatch)
    printed = _capture(monkeypatch)
    _save_session(tmp_path, style="overview", context_sends=4)
    _use_storage(monkeypatch, tmp_path, _fake_config(wechat=WeChatConfig(enabled=True)))
    monkeypatch.setattr("sys.argv", ["horizon-wechat", "-d", str(tmp_path), "status"])

    wechat_cli.main()

    joined = "\n".join(printed)
    assert "user@im.wechat" in joined and "supersecret-bot-token" not in joined and "supers…" in joined
    assert "overview (chosen in chat)" in joined and "6/10" in joined and "Ready to deliver" in joined


def test_test_dry_run_renders_messages_without_sending(monkeypatch, tmp_path):
    _silence(monkeypatch)
    printed = _capture(monkeypatch)
    sent = []

    async def record(*args, **kwargs):
        sent.append(args)

    monkeypatch.setattr("src.services.wechat.ILinkClient.send_text", record)
    _use_storage(monkeypatch, tmp_path, _fake_config(wechat=WeChatConfig(chunk_size=500)))
    monkeypatch.setattr("sys.argv", ["horizon-wechat", "-d", str(tmp_path), "test", "--dry-run", "--lang", "zh", "--style", "overview"])

    wechat_cli.main()

    assert sent == []
    text = "\n".join(printed)
    assert "Dry Run" in text and "Style: overview" in text and "Messages to send: 3" in text
    assert "No message was sent" in text


def test_test_requires_enabled_when_sending(monkeypatch, tmp_path):
    _silence(monkeypatch)
    _save_session(tmp_path)
    _use_storage(monkeypatch, tmp_path, _fake_config(wechat=WeChatConfig(enabled=False)))
    monkeypatch.setattr("sys.argv", ["horizon-wechat", "-d", str(tmp_path), "test"])

    with pytest.raises(SystemExit) as excinfo:
        wechat_cli.main()
    assert excinfo.value.code == 1


class FakeLoginClient:
    def __init__(self, statuses, qr_responses=None):
        self.statuses = list(statuses)
        self.qr_responses = list(qr_responses or [{"qrcode": "q1", "qrcode_img_content": "https://qr.example/1"}])
        self.qr_calls = []
        self.status_calls = []

    async def get_bot_qrcode(self, local_tokens):
        self.qr_calls.append(list(local_tokens))
        return self.qr_responses.pop(0) if len(self.qr_responses) > 1 else self.qr_responses[0]

    async def get_qrcode_status(self, qrcode, *, verify_code=None, base_url=None):
        self.status_calls.append({"qrcode": qrcode, "verify_code": verify_code, "base_url": base_url})
        return self.statuses.pop(0)


def test_wait_for_login_follows_redirect_and_confirms(monkeypatch):
    _silence(monkeypatch)
    monkeypatch.setattr(wechat_cli, "_render_qr", lambda content: None)

    async def no_sleep(_):
        return None

    monkeypatch.setattr(wechat_cli.asyncio, "sleep", no_sleep)
    client = FakeLoginClient(
        [
            {"status": "wait"},
            {"status": "scaned"},
            {"status": "scaned_but_redirect", "redirect_host": "sh.ilinkai.weixin.qq.com"},
            {"status": "confirmed", "bot_token": "tok", "ilink_user_id": "u@im.wechat"},
        ]
    )
    result = asyncio.run(wechat_cli._wait_for_login(client, ["old"]))

    assert result["bot_token"] == "tok" and client.qr_calls == [["old"]]
    assert client.status_calls[0]["base_url"] == ILINK_BASE_URL
    assert client.status_calls[-1]["base_url"] == "https://sh.ilinkai.weixin.qq.com"


def test_wait_for_login_refreshes_expired_qr_and_submits_verify_code(monkeypatch):
    _silence(monkeypatch)
    monkeypatch.setattr(wechat_cli, "_render_qr", lambda content: None)
    monkeypatch.setattr("builtins.input", lambda prompt="": "8888")
    client = FakeLoginClient(
        [{"status": "expired"}, {"status": "need_verifycode"}, {"status": "confirmed", "bot_token": "tok2"}],
        qr_responses=[
            {"qrcode": "q1", "qrcode_img_content": "https://qr.example/1"},
            {"qrcode": "q2", "qrcode_img_content": "https://qr.example/2"},
        ],
    )

    result = asyncio.run(wechat_cli._wait_for_login(client, []))

    assert result["bot_token"] == "tok2" and len(client.qr_calls) == 2
    assert client.status_calls[-1] == {"qrcode": "q2", "verify_code": "8888", "base_url": ILINK_BASE_URL}


def test_wait_for_login_gives_up_when_verification_blocked(monkeypatch):
    _silence(monkeypatch)
    monkeypatch.setattr(wechat_cli, "_render_qr", lambda content: None)
    assert asyncio.run(wechat_cli._wait_for_login(FakeLoginClient([{"status": "verify_code_blocked"}]), [])) is None


def test_force_login_requests_a_fresh_session(monkeypatch, tmp_path):
    """--force must not report the saved token, or WeChat keeps the old session."""
    _silence(monkeypatch)
    _save_session(tmp_path, bot_token="old-token")
    storage = StorageManager(data_dir=str(tmp_path))
    seen = {}

    async def fake_wait(client, local_tokens):
        seen["tokens"] = list(local_tokens)
        return None  # abort after recording

    monkeypatch.setattr(wechat_cli, "_wait_for_login", fake_wait)
    with pytest.raises(SystemExit):
        asyncio.run(wechat_cli._run_login(WeChatConfig(), storage, force=True))
    assert seen["tokens"] == []

    seen.clear()  # a ready session without --force returns early
    asyncio.run(wechat_cli._run_login(WeChatConfig(), storage, force=False))
    assert seen == {}


def test_login_waits_for_first_message_then_welcomes(monkeypatch, tmp_path):
    _silence(monkeypatch)
    printed = _capture(monkeypatch)
    storage = StorageManager(data_dir=str(tmp_path))
    session_path = tmp_path / "wechat_session.json"

    async def fake_wait(client, local_tokens):
        return {"status": "confirmed", "bot_token": "tok", "ilink_user_id": "u@im.wechat", "ilink_bot_id": "b@im.bot"}

    sent = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.calls = 0

        async def get_updates(self, buf, *, timeout=None):
            self.calls += 1
            return {
                "ret": 0,
                "get_updates_buf": "buf-b",
                "msgs": [{"message_type": 1, "from_user_id": "u@im.wechat", "context_token": "ctx-x"}],
            }

        async def send_text(self, to, text, *, context_token):
            sent.append((to, text, context_token))
            return {"ret": 0}

    monkeypatch.setattr(wechat_cli, "_wait_for_login", fake_wait)
    monkeypatch.setattr("src.services.wechat.ILinkClient", FakeClient)

    asyncio.run(wechat_cli._run_login(WeChatConfig(enabled=False), storage, force=False))

    saved = json.loads(session_path.read_text(encoding="utf-8"))
    assert saved["context_token"] == "ctx-x" and saved["get_updates_buf"] == "buf-b"
    assert saved["context_sends"] == 1  # the welcome counts against the budget
    assert sent[0][0] == "u@im.wechat" and sent[0][2] == "ctx-x" and "Horizon" in sent[0][1]
    assert any("Connected" in line for line in printed)


def test_listen_handles_commands_until_interrupted(monkeypatch, tmp_path):
    _silence(monkeypatch)
    printed = _capture(monkeypatch)
    _save_session(tmp_path)
    calls = {"n": 0}

    async def fake_refresh(self, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            self.session.style = "overview"
            return True
        raise KeyboardInterrupt

    async def noop(self):
        return {"ret": 0}

    monkeypatch.setattr("src.services.wechat.WeChatNotifier.refresh_context", fake_refresh)
    monkeypatch.setattr("src.services.wechat.ILinkClient.notify_start", noop)
    monkeypatch.setattr("src.services.wechat.ILinkClient.notify_stop", noop)
    _use_storage(monkeypatch, tmp_path, _fake_config(wechat=WeChatConfig(enabled=True)))
    monkeypatch.setattr("sys.argv", ["horizon-wechat", "-d", str(tmp_path), "listen"])

    with pytest.raises(SystemExit) as excinfo:
        wechat_cli.main()

    assert excinfo.value.code == 0
    joined = "\n".join(printed)
    assert "Listening" in joined and "style: overview" in joined
