"""WeChat (iLink Bot) notification service for Horizon.

WeChat exposes an official HTTP/JSON bot protocol ("iLink") at
``https://ilinkai.weixin.qq.com``. The flow Horizon relies on is:

1. ``horizon-wechat login`` fetches a QR code, the user scans it in WeChat,
   and the server returns a ``bot_token`` plus the scanning user's id.
2. Every message the user sends the bot carries a ``context_token``.
   Outbound ``sendmessage`` calls must echo one, so Horizon keeps the latest
   token on disk in the session file.
3. Before each delivery Horizon briefly long-polls ``getupdates`` to pick up
   a fresher context token and any chat commands, then sends the briefing as
   one or more text messages.
4. WeChat allows at most ``CONTEXT_MESSAGE_BUDGET`` bot replies per user
   message. The session tracks the count, deliveries are packed to fit, and
   the reader is asked to reply when the budget runs low.

Chat commands (``日报``, ``1``/``2``, ``切换``, ``样式``, ``帮助``) are answered
whenever the inbox is read: at the daily run, or instantly by
``horizon-wechat listen``. The wire format mirrors Tencent's reference client
(``@tencent-weixin/openclaw-weixin``); see ``docs/wechat.md``.
"""

import base64
import json
import logging
import os
import re
import secrets
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

import httpx
from rich.console import Console

from .._file_utils import _atomic_write_json
from ..ai.markdown_utils import clean_app_summary_markdown
from ..ai.summarizer import DailySummarizer
from ..console_icons import get_icons
from ..models import ContentItem, WeChatConfig
from ..storage.manager import StorageManager
from ..url_security import UnsafeURLError, safe_request
from .delivery import build_overview_and_items

logger = logging.getLogger(__name__)

try:  # pragma: no cover - metadata lookup is environment dependent
    from importlib.metadata import version as _pkg_version

    _HORIZON_VERSION = _pkg_version("horizon")
except Exception:  # pragma: no cover
    _HORIZON_VERSION = "0.1.0"


# ── protocol constants ──

ILINK_BASE_URL = "https://ilinkai.weixin.qq.com"
ILINK_BOT_TYPE = "3"
ILINK_APP_ID = "bot"
# Protocol revision of the reference client whose wire format we follow.
ILINK_CHANNEL_VERSION = "2.4.9"
ILINK_BOT_AGENT = f"Horizon/{_HORIZON_VERSION}"

# ``errcode -14 session timeout``: WeChat closed the bot's *receive* session
# (getupdates / notifystart). Seen after abruptly dropped long polls; the bot
# token usually still works for sendmessage, and the reference client simply
# backs off and retries with the same token.
SESSION_TIMEOUT_ERRCODE = -14
# ``ret -2 prepare failed`` on sendmessage once the reply budget is used up.
PREPARE_FAILED_RET = -2
# WeChat lets a bot send this many messages in reply to one user message.
CONTEXT_MESSAGE_BUDGET = 10
# Chunk headroom reserved for the low-budget footer.
_FOOTER_RESERVE = 120

MESSAGE_TYPE_USER = 1
MESSAGE_TYPE_BOT = 2
MESSAGE_STATE_FINISH = 2
ITEM_TYPE_TEXT = 1

API_TIMEOUT = 15.0
LONG_POLL_TIMEOUT = 35.0
# How long a delivery run waits for new inbound messages before sending.
CONTEXT_REFRESH_TIMEOUT = 8.0
# A second refresh within this window (e.g. for the next language) is skipped.
_REFRESH_REUSE_SECONDS = 60.0

SESSION_FILE = "wechat_session.json"


def tr(lang: str, zh: str, en: str) -> str:
    """Pick the Chinese or English variant of a user-facing string."""
    return zh if lang == "zh" else en


def reply_language(config: WeChatConfig) -> str:
    """Language for bot replies: Chinese whenever it is among the delivery languages."""
    languages = config.languages or []
    return "zh" if not languages or "zh" in languages else "en"


# ── message styles ──


@dataclass(frozen=True)
class MessageStyle:
    """How one language's briefing is split into WeChat messages."""

    name: str
    delivery: str  # summary, or summary_and_items
    label: dict[str, str]

    def describe(self, lang: str) -> str:
        return self.label.get(lang, self.label["en"])


# Order matters: it is the numbering shown by the style menu (1 = default).
STYLES: dict[str, MessageStyle] = {
    style.name: style
    for style in (
        MessageStyle(
            "summary",
            "summary",
            {"zh": "整份日报一条消息", "en": "the whole briefing in one message"},
        ),
        MessageStyle(
            "overview",
            "summary_and_items",
            {"zh": "先发总览，再逐条发详情", "en": "an overview, then one message per item"},
        ),
    )
}
STYLE_NAMES = list(STYLES)


# ── chat commands ──


class Command(str, Enum):
    NEWS = "news"  # replay the last briefing
    HELP = "help"
    MENU = "menu"  # list styles
    SET_STYLE = "set_style"  # argument: style name
    TOGGLE_STYLE = "toggle_style"


_COMMAND_WORDS: dict[Command, set[str]] = {
    Command.NEWS: {"news", "latest", "日报", "新闻", "最新", "今日"},
    Command.HELP: {"help", "h", "?", "？", "status", "帮助", "状态"},
    Command.MENU: {"style", "s", "样式"},
    Command.TOGGLE_STYLE: {"toggle", "switch", "切换"},
}
_STYLE_WORDS: dict[str, set[str]] = {
    "summary": {"summary", "1", "整份", "一条"},
    "overview": {"overview", "2", "总览", "逐条"},
}
_STYLE_WITH_ARG_RE = re.compile(r"^(?:style|样式|s)\s+(\S+)$")


def _resolve_style(word: str) -> Optional[str]:
    return next((name for name, words in _STYLE_WORDS.items() if word in words), None)


def parse_command(text: str) -> Optional[tuple[Command, Optional[str]]]:
    """Interpret a chat message as a command, or return None for ordinary chat.

    Command words are matched whole, case-insensitively, with an optional
    leading slash: ``日报``, ``/help``, ``样式``, ``切换``. A bare style choice
    (``1``, ``2``, ``overview``, ``总览``) or ``/style <choice>`` selects a
    style; ``/style <unknown>`` falls back to the menu.
    """
    word = (text or "").strip().lower().lstrip("/")
    if not word:
        return None
    for command, words in _COMMAND_WORDS.items():
        if word in words:
            return command, None
    match = _STYLE_WITH_ARG_RE.match(word)
    if match:
        style = _resolve_style(match.group(1))
        return (Command.SET_STYLE, style) if style else (Command.MENU, None)
    style = _resolve_style(word)
    return (Command.SET_STYLE, style) if style else None


# ── user-facing texts ──


def budget_line(remaining: int, lang: str) -> str:
    """One sentence on the WeChat reply budget and how to reset it."""
    return tr(
        lang,
        f"本轮剩余可推送 {remaining}/{CONTEXT_MESSAGE_BUDGET} 条。"
        f"微信规定你每发一条消息，机器人最多回复 {CONTEXT_MESSAGE_BUDGET} 条——"
        "**回复任意内容**即可重置并继续接收。",
        f"{remaining}/{CONTEXT_MESSAGE_BUDGET} pushes left in this conversation. WeChat allows "
        f"{CONTEXT_MESSAGE_BUDGET} bot replies per message you send — **reply with anything** "
        "to reset and keep receiving.",
    )


def budget_footer(remaining: int, lang: str) -> str:
    """The budget sentence as a quoted footer appended to the last message."""
    return f"\n\n> ⚠️ {budget_line(remaining, lang)}"


def style_menu(current: str, lang: str, remaining: Optional[int] = None) -> str:
    """Numbered style list with the current one marked."""
    lines = [tr(lang, "**Horizon 推送样式**", "**Horizon message styles**"), ""]
    for number, style in enumerate(STYLES.values(), start=1):
        marker = " ✅" if style.name == current else ""
        lines.append(f"{number}. `{style.name}` — {style.describe(lang)}{marker}")
    lines += [
        "",
        tr(
            lang,
            "回复 **1** 或 **2** 切换，或回复「切换」轮换；下次日报生效。",
            "Reply **1** or **2** to switch (or `switch` to toggle); it applies from the next briefing.",
        ),
    ]
    if remaining is not None:
        lines.append(budget_line(remaining, lang))
    return "\n".join(lines)


# (Chinese word, English word, description) for the help and welcome messages.
_COMMAND_HELP = [
    ("日报", "news", {"zh": "立即收取最近一期日报", "en": "receive the latest briefing right away"}),
    (
        "1 / 2 / 切换",
        "1 / 2 / switch",
        {"zh": "切换推送样式（整份一条 / 总览 + 逐条）", "en": "switch the style (one message / overview + items)"},
    ),
    ("样式", "style", {"zh": "查看样式菜单和剩余额度", "en": "show the style menu and replies left"}),
    ("帮助", "help", {"zh": "查看本说明", "en": "show this help"}),
]


def _command_lines(lang: str) -> List[str]:
    return [
        f"- 回复「{zh}」：{desc['zh']}" if lang == "zh" else f"- `{en}` — {desc['en']}"
        for zh, en, desc in _COMMAND_HELP
    ]


def help_text(current: str, remaining: int, lang: str) -> str:
    """Reply for ``帮助``: what the bot does, the commands, and the budget."""
    style = STYLES[current]
    return "\n".join(
        [
            tr(lang, "**Horizon 微信推送**", "**Horizon WeChat delivery**"),
            "",
            tr(lang, "Horizon 会把每日简报推送到这个会话。", "Horizon pushes the daily briefing into this chat."),
            tr(lang, f"当前样式：`{current}` — {style.describe(lang)}", f"Current style: `{current}` — {style.describe(lang)}"),
            "",
            tr(lang, "指令：", "Commands:"),
            *_command_lines(lang),
            "",
            budget_line(remaining, lang),
        ]
    )


def welcome_text(lang: str) -> str:
    """First reply after login: what to expect and the rules worth knowing."""
    return "\n".join(
        [
            tr(
                lang,
                "Horizon 已连接 ✅ 每日简报会推送到这里。",
                "Horizon connected ✅ daily briefings will arrive in this chat.",
            ),
            "",
            *_command_lines(lang),
            tr(
                lang,
                f"- 微信规定你每发一条消息，机器人最多回复 {CONTEXT_MESSAGE_BUDGET} 条；"
                "额度快用完时我会提醒，回复任意内容即可重置",
                f"- WeChat allows {CONTEXT_MESSAGE_BUDGET} bot replies per message you send; "
                "I will remind you when the budget runs low — reply with anything to reset it",
            ),
        ]
    )


# ── protocol helpers ──


def _client_version_number(version: str) -> int:
    """Encode ``MAJOR.MINOR.PATCH`` as ``0x00MMNNPP`` (iLink-App-ClientVersion)."""
    parts = [int(p) if p.isdigit() else 0 for p in version.split(".")[:3]]
    parts += [0] * (3 - len(parts))
    major, minor, patch = parts
    return ((major & 0xFF) << 16) | ((minor & 0xFF) << 8) | (patch & 0xFF)


ILINK_CLIENT_VERSION = str(_client_version_number(ILINK_CHANNEL_VERSION))


def _random_wechat_uin() -> str:
    """X-WECHAT-UIN header: random uint32 -> decimal string -> base64."""
    return base64.b64encode(str(secrets.randbits(32)).encode("utf-8")).decode("ascii")


def _client_id() -> str:
    return f"horizon:{int(time.time() * 1000)}-{secrets.token_hex(4)}"


def redact_token(token: Optional[str]) -> str:
    """Mask a credential for logs, keeping only a short prefix."""
    if not token:
        return "<none>"
    return f"{token[:6]}…" if len(token) > 6 else "***"


class ILinkError(Exception):
    """Raised when the iLink API returns an HTTP or business error."""

    def __init__(self, message: str, *, ret: int | None = None, errcode: int | None = None):
        super().__init__(message)
        self.ret = ret
        self.errcode = errcode

    @property
    def session_timeout(self) -> bool:
        return SESSION_TIMEOUT_ERRCODE in (self.ret, self.errcode)

    @property
    def budget_exhausted(self) -> bool:
        return self.ret == PREPARE_FAILED_RET

    def hint(self) -> str:
        """What the operator should do about this error (console/log wording)."""
        if self.session_timeout:
            return (
                "WeChat closed the bot's receive session (errcode -14). Sending usually still "
                "works and the session re-opens after a while; run 'horizon-wechat login --force' "
                "for a fresh one if it persists."
            )
        if self.budget_exhausted:
            return (
                f"WeChat refused the message (ret=-2): the reply budget for this conversation is "
                f"most likely used up ({CONTEXT_MESSAGE_BUDGET} bot replies per user message). Send "
                "the bot any message in WeChat, then run Horizon again."
            )
        return f"WeChat API error: {self}"


# ── session ──


@dataclass
class WeChatSession:
    """Login state written by ``horizon-wechat login`` and updated on every run."""

    bot_token: str
    base_url: str = ILINK_BASE_URL
    bot_id: str = ""
    user_id: str = ""
    context_token: str = ""
    get_updates_buf: str = ""
    logged_in_at: str = ""
    context_updated_at: str = ""
    style: str = ""  # Chosen in chat; empty = config default
    context_sends: int = 0  # Bot messages sent with the current context token

    @classmethod
    def load(cls, path: Path) -> Optional["WeChatSession"]:
        """Load a session file, returning None when it does not exist."""
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data.get("bot_token"):
            raise ValueError(f"WeChat session file is missing bot_token: {path}")
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})

    def save(self, path: Path) -> None:
        """Atomically persist the session, readable by the owner only."""
        _atomic_write_json(path, asdict(self))
        try:
            os.chmod(path, 0o600)
        except OSError:  # pragma: no cover - permission model is platform specific
            pass

    @property
    def ready(self) -> bool:
        return bool(self.bot_token and self.user_id and self.context_token)

    @property
    def remaining_budget(self) -> int:
        return max(0, CONTEXT_MESSAGE_BUDGET - self.context_sends)

    def effective_style(self, config: WeChatConfig, override: Optional[str] = None) -> MessageStyle:
        """``override`` > style chosen in chat > ``wechat.style``."""
        chosen = self.style if self.style in STYLES else ""
        return STYLES[override or chosen or config.style]

    def update_from_message(self, message: dict[str, Any]) -> bool:
        """Adopt the context token from an inbound user message; True when changed."""
        if message.get("message_type") not in (None, MESSAGE_TYPE_USER):
            return False
        token = message.get("context_token")
        sender = message.get("from_user_id") or ""
        if not token:
            return False
        if self.user_id and sender and sender != self.user_id:
            logger.debug("Ignoring context token from unexpected sender %s", sender)
            return False
        if not self.user_id and sender:
            self.user_id = sender
        if token != self.context_token:
            self.context_sends = 0  # a new user message grants a fresh reply budget
        self.context_token = token
        self.context_updated_at = datetime.now(timezone.utc).isoformat()
        return True


def _message_text(message: dict[str, Any]) -> str:
    for item in message.get("item_list") or []:
        if isinstance(item, dict) and item.get("type") == ITEM_TYPE_TEXT:
            return str((item.get("text_item") or {}).get("text") or "")
    return ""


# ── HTTP client ──


class ILinkClient:
    """Thin async client for the iLink bot endpoints Horizon needs."""

    def __init__(self, base_url: str = ILINK_BASE_URL, bot_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.bot_token = bot_token

    def _headers(self, *, json_body: bool) -> dict[str, str]:
        headers = {"iLink-App-Id": ILINK_APP_ID, "iLink-App-ClientVersion": ILINK_CLIENT_VERSION}
        if json_body:
            headers["Content-Type"] = "application/json"
            headers["AuthorizationType"] = "ilink_bot_token"
            headers["X-WECHAT-UIN"] = _random_wechat_uin()
        if self.bot_token:
            headers["Authorization"] = f"Bearer {self.bot_token}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict[str, Any]] = None,
        *,
        label: str,
        timeout: float = API_TIMEOUT,
        base_url: Optional[str] = None,
    ) -> dict[str, Any]:
        url = f"{(base_url or self.base_url).rstrip('/')}/{endpoint}"
        kwargs: dict[str, Any] = {"headers": self._headers(json_body=payload is not None)}
        if payload is not None:
            kwargs["content"] = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await safe_request(client, method, url, **kwargs)
        if response.status_code >= 400:
            raise ILinkError(f"{label} failed with HTTP {response.status_code}: {response.text[:300]}")
        try:
            data = response.json()
        except ValueError as e:
            raise ILinkError(f"{label} returned non-JSON body: {response.text[:300]}") from e
        if not isinstance(data, dict):
            raise ILinkError(f"{label} returned unexpected JSON: {str(data)[:300]}")
        return data

    async def _post(
        self, endpoint: str, payload: dict[str, Any], *, label: str, timeout: float = API_TIMEOUT
    ) -> dict[str, Any]:
        """Authenticated POST carrying ``base_info`` like the reference client."""
        body = {
            **payload,
            "base_info": {"channel_version": ILINK_CHANNEL_VERSION, "bot_agent": ILINK_BOT_AGENT},
        }
        return await self._request("POST", endpoint, body, label=label, timeout=timeout)

    @staticmethod
    def _check(data: dict[str, Any], label: str) -> dict[str, Any]:
        ret, errcode = data.get("ret"), data.get("errcode")
        if ret not in (None, 0) or errcode not in (None, 0):
            raise ILinkError(
                f"{label} failed: ret={ret} errcode={errcode} errmsg={data.get('errmsg', '')}",
                ret=ret,
                errcode=errcode,
            )
        return data

    # ── login ──

    async def get_bot_qrcode(self, local_tokens: Optional[List[str]] = None) -> dict[str, Any]:
        """Request a login QR code: ``{"qrcode", "qrcode_img_content"}``.

        ``local_tokens`` lets WeChat recognise an already-bound bot and answer
        ``binded_redirect`` instead of issuing a new token.
        """
        return await self._request(
            "POST",
            f"ilink/bot/get_bot_qrcode?bot_type={ILINK_BOT_TYPE}",
            {"local_token_list": list(local_tokens or [])[:10]},
            label="get_bot_qrcode",
        )

    async def get_qrcode_status(
        self, qrcode: str, *, verify_code: Optional[str] = None, base_url: Optional[str] = None
    ) -> dict[str, Any]:
        """Long-poll the QR login status; a client timeout surfaces as ``{"status": "wait"}``."""
        params = {"qrcode": qrcode, **({"verify_code": verify_code} if verify_code else {})}
        try:
            return await self._request(
                "GET",
                f"ilink/bot/get_qrcode_status?{httpx.QueryParams(params)}",
                label="get_qrcode_status",
                timeout=LONG_POLL_TIMEOUT + 5,
                base_url=base_url,
            )
        except httpx.TimeoutException:
            return {"status": "wait"}

    # ── lifecycle ──

    async def notify_start(self) -> dict[str, Any]:
        return await self._post("ilink/bot/msg/notifystart", {}, label="notifystart")

    async def notify_stop(self) -> dict[str, Any]:
        return await self._post("ilink/bot/msg/notifystop", {}, label="notifystop")

    # ── messaging ──

    async def get_updates(
        self, get_updates_buf: str = "", *, timeout: float = LONG_POLL_TIMEOUT
    ) -> dict[str, Any]:
        """Long-poll for inbound messages; a client timeout is an empty result."""
        try:
            data = await self._post(
                "ilink/bot/getupdates",
                {"get_updates_buf": get_updates_buf or ""},
                label="getupdates",
                timeout=timeout,
            )
        except httpx.TimeoutException:
            return {"ret": 0, "msgs": [], "get_updates_buf": get_updates_buf}
        return self._check(data, "getupdates")

    async def send_text(
        self, to_user_id: str, text: str, *, context_token: Optional[str]
    ) -> dict[str, Any]:
        """Send one text message to a user."""
        if not context_token:
            logger.warning("Sending WeChat message without context_token; delivery may fail")
        message: dict[str, Any] = {
            "from_user_id": "",
            "to_user_id": to_user_id,
            "client_id": _client_id(),
            "message_type": MESSAGE_TYPE_BOT,
            "message_state": MESSAGE_STATE_FINISH,
            "item_list": [{"type": ITEM_TYPE_TEXT, "text_item": {"text": text}}],
        }
        if context_token:
            message["context_token"] = context_token
        data = await self._post("ilink/bot/sendmessage", {"msg": message}, label="sendmessage")
        return self._check(data, "sendmessage")


# ── text formatting ──

_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_TOC_LINK_RE = re.compile(r"\[([^\]]+)\]\(#[^)]*\)")
_H5_H6_RE = re.compile(r"^#{5,6}[ \t]+", re.MULTILINE)
_CJK_RE = re.compile(r"[⺀-鿿가-힯豈-﫿]")
_STAR_ITALIC_RE = re.compile(r"(?<![*\w\\])\*(?!\*)([^*\n]+?)(?<!\\)\*(?![*\w])")
_UNDERSCORE_ITALIC_RE = re.compile(r"(?<![_\w\\])_(?!_)([^_\n]+?)(?<!\\)_(?![_\w])")


def _unwrap_cjk_italics(match: re.Match) -> str:
    content = match.group(1)
    return content if _CJK_RE.search(content) else match.group(0)


def format_markdown_for_wechat(value: str) -> str:
    """Prepare briefing Markdown for the WeChat bot chat renderer.

    WeChat renders a Markdown subset: headings up to H4, bold, links, inline
    code, fenced code, tables, and rules. Mirroring the reference client's
    filter, drop images, flatten H5/H6 to text, and unwrap italics around CJK
    text (which WeChat does not render). In-page anchor links from the table
    of contents are reduced to their text.
    """
    value = clean_app_summary_markdown(value)
    value = _IMAGE_RE.sub("", value)
    value = _TOC_LINK_RE.sub(r"\1", value)
    value = _H5_H6_RE.sub("", value)
    value = _STAR_ITALIC_RE.sub(_unwrap_cjk_italics, value)
    value = _UNDERSCORE_ITALIC_RE.sub(_unwrap_cjk_italics, value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def _pack(units: List[str], sep: str, limit: int) -> List[str]:
    """Greedily join *units* with *sep* into strings of at most *limit* chars."""
    packed: List[str] = []
    current = ""
    for unit in units:
        candidate = unit if not current else f"{current}{sep}{unit}"
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            packed.append(current)
        current = unit
    if current:
        packed.append(current)
    return packed


def split_text_chunks(text: str, limit: int) -> List[str]:
    """Split text into chunks of at most *limit* characters.

    Prefers paragraph boundaries, then line boundaries, and only hard-splits a
    single overlong line as a last resort.
    """
    if limit <= 0:
        raise ValueError("limit must be positive")
    text = text.strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    result: List[str] = []
    for paragraph_chunk in _pack(text.split("\n\n"), "\n\n", limit):
        if len(paragraph_chunk) <= limit:
            result.append(paragraph_chunk)
            continue
        for line_chunk in _pack(paragraph_chunk.split("\n"), "\n", limit):
            if len(line_chunk) <= limit:
                result.append(line_chunk)
            else:
                result.extend(line_chunk[i : i + limit] for i in range(0, len(line_chunk), limit))
    return [chunk.strip() for chunk in result if chunk.strip()]


def pack_chunks(bodies: List[str], limit: int, max_messages: int) -> List[str]:
    """Turn message bodies into at most *max_messages* chunks when possible.

    Each body normally becomes its own message (chunked at *limit*). When that
    needs more messages than allowed, consecutive bodies are merged, separated
    by a rule, and the result is chunked again.
    """
    separate = [chunk for body in bodies for chunk in split_text_chunks(body, limit)]
    if len(separate) <= max(max_messages, 1):
        return separate
    merged = _pack([body.strip() for body in bodies if body.strip()], "\n\n---\n\n", limit)
    return [chunk for body in merged for chunk in split_text_chunks(body, limit)]


# ── delivery ──


class WeChatDeliveryStatus(str, Enum):
    DISABLED = "disabled"
    SKIPPED = "skipped"
    SUCCESS = "success"
    PLATFORM_FAILURE = "platform_failure"
    NETWORK_FAILURE = "network_failure"
    INTERNAL_FAILURE = "internal_failure"


@dataclass(frozen=True)
class WeChatDeliveryResult:
    status: WeChatDeliveryStatus
    detail: str | None = None
    chunks_sent: int = 0

    @property
    def sent(self) -> bool:
        return self.status == WeChatDeliveryStatus.SUCCESS


@dataclass
class Briefing:
    """One language's briefing in both layouts, cached for the ``日报`` replay."""

    date: str
    lang: str
    summary: str
    overview: str = ""
    items: List[str] = field(default_factory=list)
    saved_at: str = ""

    @staticmethod
    def path(data_dir: Path, lang: str) -> Path:
        return Path(data_dir) / f"wechat_briefing-{lang}.json"

    @classmethod
    def compose(
        cls,
        summarizer: DailySummarizer,
        summary: str,
        important_items: List[ContentItem],
        all_items_count: int,
        date: str,
        lang: str,
    ) -> "Briefing":
        overview, items = build_overview_and_items(
            summarizer, important_items, all_items_count, date, lang
        )
        return cls(date=date, lang=lang, summary=summary, overview=overview, items=items)

    @classmethod
    def load(cls, data_dir: Path, lang: str) -> Optional["Briefing"]:
        path = cls.path(data_dir, lang)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            logger.warning("Could not read briefing cache %s: %s", path, e)
            return None
        if not isinstance(data, dict) or not data.get("summary"):
            return None
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})

    def save(self, data_dir: Path) -> None:
        self.saved_at = datetime.now(timezone.utc).isoformat()
        _atomic_write_json(self.path(data_dir, self.lang), asdict(self))

    def bodies(self, style: MessageStyle) -> List[str]:
        """Message bodies for *style*; item texts already carry their "Item i/n" lead."""
        if style.delivery == "summary_and_items" and self.items:
            return [self.overview, *self.items]
        return [self.summary]


class WeChatNotifier:
    """Sends the daily briefing to a WeChat user through the iLink bot API."""

    def __init__(self, config: WeChatConfig, storage: StorageManager, console=None, icons=None):
        self.config = config
        self.storage = storage
        self.console = console if console is not None else Console(stderr=True)
        self.icons = icons if icons is not None else get_icons()
        self.data_dir = Path(storage.data_dir)
        self.session_path = self.data_dir / SESSION_FILE
        self.session: Optional[WeChatSession] = None
        self._refreshed_at = 0.0
        self.reload_session()
        if self.session is None:
            logger.warning("WeChat enabled but %s is missing, skipping notification.", self.session_path)
            self.console.print(
                f"[yellow]WeChat enabled but '{self.session_path}' does not exist. "
                f"Run 'horizon-wechat login' to connect. Skipping notification.[/yellow]"
            )

    # ── session ──

    def reload_session(self) -> None:
        """Re-read the session file; ``horizon-wechat listen`` may have updated it."""
        try:
            self.session = WeChatSession.load(self.session_path)
        except (OSError, ValueError) as e:
            logger.warning("Could not read WeChat session %s: %s", self.session_path, e)
            self.console.print(
                f"[yellow]WeChat session file '{self.session_path}' could not be read ({e}). "
                "Run 'horizon-wechat login'.[/yellow]"
            )

    def _save_session(self) -> None:
        if self.session is not None:
            self.session.save(self.session_path)

    def style(self, override: Optional[str] = None) -> MessageStyle:
        if self.session is None:
            return STYLES[override or self.config.style]
        return self.session.effective_style(self.config, override)

    def client(self) -> ILinkClient:
        if self.session is None:
            raise RuntimeError("WeChat session is not loaded")
        return ILinkClient(self.session.base_url, self.session.bot_token)

    # ── inbox ──

    async def _send_counted(self, text: str) -> None:
        """Send one message and record it against the reply budget."""
        assert self.session is not None
        try:
            await self.client().send_text(
                self.session.user_id, text, context_token=self.session.context_token
            )
        except ILinkError as e:
            if e.budget_exhausted:  # the server is the authority; sync our counter
                self.session.context_sends = CONTEXT_MESSAGE_BUDGET
                self._save_session()
            raise
        self.session.context_sends += 1
        self._save_session()

    async def _reply(self, text: str) -> None:
        try:
            await self._send_counted(text)
        except (ILinkError, httpx.HTTPError, UnsafeURLError) as e:
            logger.warning("Could not answer chat command: %s", e)

    async def _handle_command(self, text: str) -> bool:
        """Answer a chat command; True when the session changed (style switched)."""
        assert self.session is not None
        parsed = parse_command(text)
        if parsed is None:
            return False
        command, arg = parsed
        lang = reply_language(self.config)
        remaining_after_reply = max(0, self.session.remaining_budget - 1)
        current = self.style().name

        if command is Command.NEWS:
            await self._send_latest_briefing(lang)
            return False
        if command is Command.HELP:
            await self._reply(help_text(current, remaining_after_reply, lang))
            return False
        if command is Command.MENU:
            await self._reply(style_menu(current, lang, remaining_after_reply))
            return False

        if command is Command.SET_STYLE:
            new_style = arg or current
        else:
            new_style = STYLE_NAMES[(STYLE_NAMES.index(current) + 1) % len(STYLE_NAMES)]
        self.session.style = new_style
        label = STYLES[new_style].describe(lang)
        await self._reply(
            tr(
                lang,
                f"已切换为 `{new_style}`：{label}。下次日报生效。",
                f"Switched to `{new_style}`: {label}. Applies from the next briefing.",
            )
        )
        return True

    async def _send_latest_briefing(self, lang: str) -> None:
        """Replay the last delivered briefing in the active style (no AI call)."""
        briefing = Briefing.load(self.data_dir, lang)
        if briefing is None:
            saved = self.storage.latest_daily_summary(lang)
            if saved is not None:
                briefing = Briefing(date=saved[0], lang=lang, summary=saved[1])
        if briefing is None:
            bodies = [
                tr(
                    lang,
                    "还没有生成过日报。等 Horizon 跑完第一次任务后再试。",
                    "No briefing has been generated yet. Try again after Horizon's first run.",
                )
            ]
        else:
            bodies = briefing.bodies(self.style())
        for chunk in self.plan_chunks(bodies, lang):
            await self._reply(chunk)

    async def refresh_context(self, timeout: float = CONTEXT_REFRESH_TIMEOUT) -> bool:
        """Drain pending inbound messages: newest context token and chat commands.

        Returns True when the session changed. Raises ILinkError when WeChat
        rejects the poll (for example ``errcode -14``).
        """
        if self.session is None:
            return False
        data = await self.client().get_updates(self.session.get_updates_buf, timeout=timeout)
        self._refreshed_at = time.monotonic()
        changed = False
        for message in data.get("msgs") or []:
            if isinstance(message, dict) and self.session.update_from_message(message):
                changed = True
                changed |= await self._handle_command(_message_text(message))
        new_buf = data.get("get_updates_buf")
        if new_buf and new_buf != self.session.get_updates_buf:
            self.session.get_updates_buf = new_buf
            changed = True
        if changed:
            self._save_session()
        return changed

    async def _refresh_before_send(self) -> None:
        """Pick up commands and a fresher token; never blocks delivery."""
        if time.monotonic() - self._refreshed_at < _REFRESH_REUSE_SECONDS:
            return
        self.reload_session()
        try:
            await self.refresh_context()
        except ILinkError as e:
            self.console.print(f"[yellow]WeChat inbox check skipped: {e.hint()}[/yellow]")
            logger.warning("WeChat getupdates failed, using stored context: %s", e)
        except (httpx.HTTPError, UnsafeURLError) as e:
            logger.warning("WeChat getupdates network error, using stored context: %s", e)

    # ── sending ──

    def plan_chunks(self, bodies: List[str], lang: str) -> List[str]:
        """Render bodies into the messages to send, fitted to the reply budget.

        Bodies are packed together when they would exceed the remaining budget,
        and a footer asking the reader to reply is appended when the budget is
        about to run out.
        """
        remaining = self.session.remaining_budget if self.session else CONTEXT_MESSAGE_BUDGET
        limit = max(1, self.config.chunk_size - _FOOTER_RESERVE)
        chunks = pack_chunks([format_markdown_for_wechat(body) for body in bodies], limit, remaining)
        if not chunks:
            return []
        if len(chunks) > remaining:
            logger.warning(
                "WeChat delivery needs %d messages but only %d replies remain", len(chunks), remaining
            )
        left_after = remaining - len(chunks)
        if left_after <= 2:
            chunks[-1] += budget_footer(max(left_after, 0), lang)
        return chunks

    def _not_ready(self) -> Optional[WeChatDeliveryResult]:
        if not self.config.enabled:
            return WeChatDeliveryResult(WeChatDeliveryStatus.DISABLED)
        if self.session is None:
            return WeChatDeliveryResult(
                WeChatDeliveryStatus.SKIPPED, detail=f"'{self.session_path}' is missing"
            )
        if not self.session.ready:
            hint = (
                "no context token yet — send the bot any message in WeChat, "
                "then run 'horizon-wechat status --refresh'"
                if self.session.user_id
                else "login incomplete — run 'horizon-wechat login'"
            )
            self.console.print(f"[yellow]WeChat session not ready ({hint}). Skipping.[/yellow]")
            return WeChatDeliveryResult(WeChatDeliveryStatus.SKIPPED, detail=hint)
        return None

    async def _deliver(self, bodies: List[str], lang: str) -> WeChatDeliveryResult:
        """Send *bodies* in order, stopping at the first failure."""
        chunks = self.plan_chunks(bodies, lang)
        sent = 0
        try:
            for chunk in chunks:
                await self._send_counted(chunk)
                sent += 1
        except ILinkError as e:
            status, message = WeChatDeliveryStatus.PLATFORM_FAILURE, e.hint()
        except (httpx.HTTPError, UnsafeURLError) as e:
            status, message = WeChatDeliveryStatus.NETWORK_FAILURE, f"WeChat request failed: {e}"
        except Exception as e:  # noqa: BLE001 - every failure is reported as a result
            status = WeChatDeliveryStatus.INTERNAL_FAILURE
            message = f"WeChat delivery failed unexpectedly: {type(e).__name__}: {e}"
        else:
            logger.info("WeChat: sent %d message(s) to %s", sent, self.session.user_id)
            return WeChatDeliveryResult(WeChatDeliveryStatus.SUCCESS, chunks_sent=sent)
        self.console.print(f"[red]{message}[/red]")
        logger.error("WeChat delivery failed after %d/%d messages: %s", sent, len(chunks), message)
        return WeChatDeliveryResult(status, detail=message, chunks_sent=sent)

    async def send_text(self, markdown_text: str, lang: str = "zh") -> WeChatDeliveryResult:
        """Send one Markdown body, splitting it into chunks as needed."""
        blocker = self._not_ready()
        if blocker is not None:
            return blocker
        await self._refresh_before_send()
        return await self._deliver([markdown_text], lang)

    async def send_daily_summary(
        self,
        summary: str,
        important_items: List[ContentItem],
        all_items_count: int,
        date: str,
        lang: str,
        summarizer: DailySummarizer,
        *,
        style: Optional[str] = None,
        remember: bool = True,
    ) -> WeChatDeliveryResult:
        """Send the daily briefing for one language.

        ``style`` overrides both the chat choice and ``wechat.style``.
        ``remember`` caches the briefing for the ``日报`` command; sample sends
        (``horizon-wechat test``) pass False so they never replace a real one.
        """
        if self.config.languages and lang not in self.config.languages:
            self.console.print(
                f"{self.icons['webhook_skip']} Skipping {lang.upper()} WeChat notification "
                "(filtered by wechat.languages)"
            )
            return WeChatDeliveryResult(WeChatDeliveryStatus.SKIPPED, detail="language filtered")
        blocker = self._not_ready()
        if blocker is not None:
            return blocker

        briefing = Briefing.compose(summarizer, summary, important_items, all_items_count, date, lang)
        if remember:
            try:
                briefing.save(self.data_dir)
            except OSError as e:
                logger.warning("Could not cache briefing for replay: %s", e)

        self.console.print(f"{self.icons['wechat']} Sending {lang.upper()} WeChat notification...")
        await self._refresh_before_send()  # a style switched in chat just now applies below
        result = await self._deliver(briefing.bodies(self.style(style)), lang)
        if result.sent:
            self.console.print(
                f"[green]WeChat notification sent ({result.chunks_sent} message(s), "
                f"{self.session.remaining_budget} replies left for this conversation)[/green]"
            )
        return result

    async def send_failure(self, date: str, error_message: str) -> WeChatDeliveryResult:
        """Notify the user that the pipeline failed."""
        blocker = self._not_ready()
        if blocker is not None:
            return blocker
        self.console.print(f"{self.icons['wechat']} Sending WeChat failure notification...")
        await self._refresh_before_send()
        return await self._deliver(
            [f"**Horizon generation failed** ({date})\n\n{error_message}"], reply_language(self.config)
        )
