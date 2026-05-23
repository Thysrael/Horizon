"""Webhook notification service for Horizon."""

import json
import logging
import os
import re
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime, timezone
from typing import Any, List, Optional, Union, cast
from urllib.parse import urlparse
import httpx

from ..ai.markdown_utils import clean_app_summary_markdown
from ..models import ContentItem, WebhookConfig
from ..ai.summarizer import DailySummarizer

logger = logging.getLogger(__name__)


# Pattern: #{key} or #{key?param1=val1&param2=val2}
_PLACEHOLDER_RE = re.compile(r"#\{(\w+)(\?\w+=[^}]+)?\}")
_SENSITIVE_HEADER_RE = re.compile(
    r"(authorization|token|secret|signature|key|password)", re.IGNORECASE
)


def _truncate(value: str, limit: int, split: str) -> str:
    """Truncate a string to at most *limit* characters by splitting on *split*.

    Segments are accumulated in order until adding the next one would
    exceed *limit* characters.  Remaining segments are dropped.

    Args:
        value: The full text to truncate
        limit: Maximum number of characters allowed
        split: Delimiter to split value into segments

    Returns:
        Truncated text
    """
    segments = value.split(split)
    kept: list[str] = []
    current_chars = 0

    for seg in segments:
        # +len(split) for the delimiter that will be re-joined
        seg_chars = len(seg) + (len(split) if kept else 0)
        if kept and current_chars + seg_chars > limit:
            break
        kept.append(seg)
        current_chars += seg_chars

    return split.join(kept)


def _render(
    template: Union[str, dict, list], variables: dict
) -> Union[str, dict, list]:
    """Replace #{key} and #{key?params} placeholders in a template.

    Supports strings, dicts, and lists.  For dicts/lists, walks all
    string values recursively and replaces placeholders.

    Parameterized syntax: #{key?limit=N&split=DELIM}
      - limit: maximum number of output characters
      - split: delimiter to split the value into segments before
               accumulating up to *limit* characters

    Args:
        template: Template with #{key} placeholders — str, dict, or list
        variables: Dict mapping placeholder keys to replacement values

    Returns:
        Same type as template, with placeholders replaced
    """
    if isinstance(template, dict):
        return {k: _render(v, variables) for k, v in template.items()}
    if isinstance(template, list):
        return [_render(item, variables) for item in template]
    if isinstance(template, str):

        def _replace(match: re.Match) -> str:
            key = match.group(1)
            params_str = match.group(2)  # e.g. "?limit=500&split=---"

            value = variables.get(key)
            if value is None:
                return match.group(0)  # leave placeholder unchanged

            if not params_str:
                return str(value)

            # Parse params: ?limit=500&split=---
            raw_params = params_str.lstrip("?")
            params: dict[str, str] = {}
            for pair in raw_params.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v

            limit = int(params.get("limit", "0")) if "limit" in params else 0
            split_delim = params.get("split", "---")

            if limit and split_delim:
                return _truncate(str(value), limit, split_delim)

            return str(value)

        return _PLACEHOLDER_RE.sub(_replace, template)
    # int, float, bool, None — return as-is
    return template


def _format_markdown_for_webhook(value: str) -> str:
    """Flatten HTML constructs that chat/webhook Markdown often cannot render."""
    return clean_app_summary_markdown(value)


def _prepare_variables_for_body(
    raw_body: Union[str, dict, list, None], variables: dict
) -> dict:
    """Apply webhook-safe variable formatting before body rendering."""
    if raw_body is None or "summary" not in variables:
        return variables

    prepared = dict(variables)
    prepared["summary"] = _format_markdown_for_webhook(str(variables["summary"]))
    return prepared


def _isjson(s: str) -> bool:
    """Return True if the string starts with a JSON open brace."""
    s = s.strip()
    return s.startswith("{") or s.startswith("[")


def _is_feishu_platform(platform: str) -> bool:
    """Return whether platform should use Feishu/Lark card rendering."""
    return platform.lower() in {"feishu", "lark"}


def _text(value: str) -> dict[str, str]:
    """Build a Feishu plain text object."""
    return {"tag": "plain_text", "content": value}


def _markdown(content: str) -> dict[str, str]:
    """Build a Feishu Markdown component."""
    return {"tag": "markdown", "content": content}


def _collapsible_panel(title: str, content: str) -> dict[str, Any]:
    """Build a Feishu Card JSON 2.0 collapsible panel."""
    return {
        "tag": "collapsible_panel",
        "expanded": False,
        "header": {
            "title": _text(title),
            "icon": {
                "tag": "standard_icon",
                "token": "down-small-ccm_outlined",
                "size": "16px 16px",
            },
            "icon_position": "right",
            "icon_expanded_angle": -180,
        },
        "border": {"color": "grey", "corner_radius": "5px"},
        "elements": [_markdown(content)],
    }


def _extract_headers(headers_str: Optional[str]) -> dict:
    """Parse custom headers from a multi-line "Key: Value" string.

    Args:
        headers_str: Multi-line string, each line "Key: Value"

    Returns:
        dict: Parsed headers as key-value pairs
    """
    if not headers_str:
        return {}

    headers = {}
    for line in headers_str.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":", 1)
        if len(parts) != 2:
            logger.warning("Invalid webhook header line: %s", line)
            continue
        k, v = parts[0].strip(), parts[1].strip()
        headers[k] = v

    return headers


def redact_url(url: str) -> str:
    """Return a log-safe URL without query strings or fragments."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return "<invalid-url>"
    if not parts.scheme or not parts.netloc:
        return "<redacted-url>"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """Mask sensitive header values for logs and dry-run output."""
    return {
        key: "<redacted>" if _SENSITIVE_HEADER_RE.search(key) else value
        for key, value in headers.items()
    }


class WebhookNotifier:
    """Sends webhook notifications after pipeline completion or failure."""

    def __init__(self, config: WebhookConfig, console=None):
        self.config = config
        if console is None:
            try:
                from rich.console import Console

                self.console = Console()
            except ImportError:

                class DummyConsole:
                    def print(self, *args, **kwargs):
                        print(*args, **kwargs)

                self.console = DummyConsole()
        else:
            self.console = console
        self.url = None
        self._validate_config()  # sets self.url or raises ValueError

    def _validate_url(self, url: str) -> str:
        """Validate webhook URL has a valid scheme (http/https) and hostname.
        Raises:
            ValueError: If the URL is empty, has wrong scheme, no hostname,
                        or is structurally invalid
        """
        url = url.strip()
        # Remove shell escape artifacts: \? \= \& \% before query chars
        url = re.sub(r"\\([?=&%])", r"\1", url)
        if not url:
            raise ValueError(
                f"Webhook URL is empty (env var '{self.config.url_env}' is set but empty)"
            )
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"Webhook URL must use http or https scheme, got '{parsed.scheme or 'none'}' "
                f"(env var '{self.config.url_env}')"
            )
        if not parsed.hostname:
            raise ValueError(
                f"Webhook URL has no hostname: '{url}' "
                f"(env var '{self.config.url_env}')"
            )
        try:
            httpx.URL(url)
        except httpx.InvalidURL as e:
            raise ValueError(
                f"Webhook URL is structurally invalid: '{url}' — {e} "
                f"(env var '{self.config.url_env}')"
            ) from e
        return url

    def _validate_config(self) -> None:
        """Validate webhook URL configuration and print warnings for skip scenarios.

        Raises ValueError when URL is present but invalid.
        Sets self.url to the validated URL, or leaves it None for skip scenarios.
        """
        if not self.config.url_env:
            # url_env not configured at all
            logger.warning("Webhook enabled but url_env is not configured, skipping notification.")
            self.console.print(
                "[yellow]Webhook enabled but 'url_env' is not set in config. "
                "No notification URL available, skipping.[/yellow]"
            )
            return

        raw_url = os.getenv(self.config.url_env)
        if raw_url is None:
            # env var name configured, but the env var itself doesn't exist
            logger.warning(
                "Webhook enabled but env var '%s' is not set, skipping notification.",
                self.config.url_env,
            )
            self.console.print(
                f"[yellow]Webhook enabled but env var '{self.config.url_env}' is not set "
                f"in your environment. Skipping notification.[/yellow]"
            )
            return

        # env var exists — validate the URL value (strip + scheme + hostname + httpx check)
        self.url = self._validate_url(raw_url)

    def _render_request_components(
        self, variables: dict
    ) -> tuple[str, str | None, dict[str, str]]:
        """Render the final request URL, body, and headers for the given variables."""
        request_url = cast(str, _render(self.url or "", variables))

        content_type = "application/x-www-form-urlencoded"
        body_content = None
        raw_body = variables.get("_request_body_override", self.config.request_body)
        body_variables = _prepare_variables_for_body(raw_body, variables)

        if raw_body:
            if isinstance(raw_body, (dict, list)):
                rendered_obj = _render(raw_body, body_variables)
                body_content = json.dumps(rendered_obj, ensure_ascii=False)
                content_type = "application/json"
            elif isinstance(raw_body, str) and raw_body.strip():
                rendered = cast(str, _render(raw_body, body_variables))
                body_content = rendered
                if _isjson(rendered):
                    try:
                        json.loads(rendered)
                        content_type = "application/json"
                    except json.JSONDecodeError:
                        pass

        headers = _extract_headers(self.config.headers)
        headers["Content-Type"] = content_type
        return request_url, body_content, headers

    def _can_use_feishu_collapsible(self) -> bool:
        """Return whether this notifier should render Feishu collapsible cards."""
        platform = getattr(self.config, "platform", "generic")
        layout = getattr(self.config, "layout", "markdown")
        return _is_feishu_platform(platform) and layout == "collapsible"

    def _build_feishu_collapsible_overview(
        self,
        item_count: int,
        all_items_count: int,
        date: str,
        lang: str,
    ) -> str:
        """Build a non-redundant overview for a card that already lists item panels."""
        if lang == "zh":
            if item_count == 0:
                return (
                    f"# Horizon 每日速递 - {date}\n\n"
                    f"> 已分析 {all_items_count} 条内容，暂无达到重要性阈值的资讯。"
                )
            return (
                f"# Horizon 每日速递 - {date}\n\n"
                f"> 从 {all_items_count} 条内容中筛选出 {item_count} 条重要资讯。\n\n"
                "点击下方新闻面板即可在飞书内展开阅读全文。"
            )

        if item_count == 0:
            return (
                f"# Horizon Daily - {date}\n\n"
                f"> Analyzed {all_items_count} items, but none met the importance threshold."
            )

        return (
            f"# Horizon Daily - {date}\n\n"
            f"> Selected {item_count} important items from {all_items_count} fetched items.\n\n"
            "Expand the panels below to read the full briefing inside Feishu/Lark."
        )

    def _build_feishu_collapsible_body(
        self,
        important_items: List[ContentItem],
        all_items_count: int,
        date: str,
        lang: str,
        summarizer: DailySummarizer,
    ) -> dict[str, Any]:
        """Build a single Feishu Card JSON 2.0 message with collapsed item details."""
        overview = self._build_feishu_collapsible_overview(
            item_count=len(important_items),
            all_items_count=all_items_count,
            date=date,
            lang=lang,
        )
        elements: list[dict[str, Any]] = [_markdown(overview)]

        for item_index, item in enumerate(important_items, start=1):
            title = str(item.metadata.get(f"title_{lang}") or item.title)
            score = item.ai_score or "?"
            panel_title = f"{item_index}. {title} ⭐️ {score}/10"
            item_content = summarizer.generate_webhook_item(
                item,
                language=lang,
                index=item_index,
                total=len(important_items),
            )
            elements.append(
                _collapsible_panel(
                    panel_title,
                    _format_markdown_for_webhook(item_content),
                )
            )

        return {
            "msg_type": "interactive",
            "card": {
                "schema": "2.0",
                "config": {
                    "wide_screen_mode": True,
                    "update_multi": True,
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": (
                            f"Horizon {date} 折叠日报"
                            if lang == "zh"
                            else f"Horizon {date} Collapsible Daily"
                        ),
                    },
                    "template": "blue",
                },
                "body": {
                    "elements": elements,
                },
            },
        }

    def build_preview(self, variables: dict) -> dict[str, Any]:
        """Build the fully rendered request for dry-run preview."""
        request_url, body_content, headers = self._render_request_components(variables)
        return {
            "url": redact_url(request_url),
            "body": body_content,
            "headers": redact_headers(headers),
        }

    def build_daily_summary_messages(
        self,
        summary: str,
        important_items: List[ContentItem],
        all_items_count: int,
        date: str,
        lang: str,
        summarizer: DailySummarizer,
    ) -> List[dict[str, Any]]:
        """Build the variables for all webhook messages for one language."""
        webhook_languages = getattr(self.config, "languages", None)
        if webhook_languages and lang not in webhook_languages:
            return []

        base_vars = {
            "date": date,
            "language": lang,
            "important_items": len(important_items),
            "all_items": all_items_count,
            "result": "success",
            "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
        }

        if self._can_use_feishu_collapsible():
            return [
                {
                    **base_vars,
                    "message_title": (
                        f"Horizon {date} 折叠日报"
                        if lang == "zh"
                        else f"Horizon {date} Collapsible Daily"
                    ),
                    "message_kind": "collapsible",
                    "summary": self._build_feishu_collapsible_overview(
                        item_count=len(important_items),
                        all_items_count=all_items_count,
                        date=date,
                        lang=lang,
                    ),
                    "_request_body_override": self._build_feishu_collapsible_body(
                        important_items=important_items,
                        all_items_count=all_items_count,
                        date=date,
                        lang=lang,
                        summarizer=summarizer,
                    ),
                }
            ]

        delivery = getattr(self.config, "delivery", "summary")
        if delivery == "summary_and_items":
            item_messages: List[dict[str, Any]] = []
            overview = summarizer.generate_webhook_overview(
                important_items,
                date,
                all_items_count,
                language=lang,
            )
            overview_message = {
                **base_vars,
                "message_title": (
                    f"Horizon {date} 总览"
                    if lang == "zh"
                    else f"Horizon {date} Overview"
                ),
                "message_kind": "overview",
                "summary": overview,
            }
            for item_index, item in enumerate(important_items, start=1):
                title = str(item.metadata.get(f"title_{lang}") or item.title)
                item_summary = summarizer.generate_webhook_item(
                    item,
                    language=lang,
                    index=item_index,
                    total=len(important_items),
                )
                item_messages.append(
                    {
                        **base_vars,
                        "message_title": f"{item_index}/{len(important_items)} {title}",
                        "message_kind": "item",
                        "item_index": item_index,
                        "item_count": len(important_items),
                        "item_title": title,
                        "item_url": str(item.url),
                        "item_score": item.ai_score or "",
                        "summary": item_summary,
                    }
                )

            if getattr(self.config, "overview_position", "first") == "last":
                return list(reversed(item_messages)) + [overview_message]

            return [overview_message] + item_messages

        return [
            {
                **base_vars,
                "message_title": (
                    f"Horizon {date} 日报" if lang == "zh" else f"Horizon {date} Daily"
                ),
                "message_kind": "summary",
                "summary": summary,
            }
        ]

    async def notify(self, variables: dict) -> None:
        """Send a webhook notification with template variable substitution.

        If request_body is empty, sends a GET request.
        If request_body is provided, sends a POST request with
        auto-detected content-type

        Args:
            variables: Dict of template variable values to replace
                       in URL, request_body, and headers.
        """
        if not self.config.enabled:
            self.console.print("[yellow]Webhook is disabled, skipping notification.[/yellow]")
            return

        if not self.url:
            logger.warning(
                "Webhook enabled but URL is empty (env var %s not set), skipping notification.",
                self.config.url_env,
            )
            self.console.print(
                f"[yellow]Webhook enabled but URL is empty — "
                f"env var '{self.config.url_env}' is not set. Skipping notification.[/yellow]"
            )
            return

        request_url, body_content, headers = self._render_request_components(variables)
        safe_url = redact_url(request_url)
        if body_content is not None:
            logger.debug(
                "Webhook POST body (%d chars): %s",
                len(body_content or ""),
                (body_content or "")[:2000],
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if body_content is None:
                    response = await client.get(request_url, headers=headers)
                else:
                    response = await client.post(
                        request_url,
                        content=body_content.encode("utf-8"),
                        headers=headers,
                    )

            self._handle_response_status(response, safe_url)

        except httpx.InvalidURL as e:
            self.console.print(
                f"[red]Webhook URL is invalid: {e}[/red]"
            )
            logger.error("Webhook URL invalid: %s, env var: %s", e, self.config.url_env)
        except httpx.ConnectError as e:
            self.console.print(
                f"[red]Webhook connection failed: {e}[/red]"
            )
            logger.error("Webhook connection failed: URL=%s, error=%s", safe_url, e)
        except httpx.TimeoutException as e:
            self.console.print(
                f"[red]Webhook request timed out: {e}[/red]"
            )
            logger.error("Webhook timeout: URL=%s, error=%s", safe_url, e)
        except Exception as e:
            self.console.print(
                f"[red]Webhook call failed unexpectedly: {type(e).__name__}: {e}[/red]"
            )
            logger.error("Webhook unexpected error: URL=%s, type=%s, error=%s", safe_url, type(e).__name__, e)

    def _check_body_error_code(self, body: str) -> Optional[str]:
        """Check if a 2xx response body contains a platform-specific error code.

        Returns a descriptive string if an error is detected, or None if the
        response appears successful.

        Checked patterns:
        - Feishu/Lark: {"code": non-zero, "msg": "..."} or {"StatusCode": non-zero}
        - DingTalk: {"errcode": non-zero, "errmsg": "..."}
        - Slack/Discord: {"ok": false}
        """
        try:
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return None

        # Feishu/Lark: "code" or "StatusCode" field
        feishu_code = data.get("code") or data.get("StatusCode")
        if feishu_code is not None and feishu_code != 0:
            msg = data.get("msg") or data.get("StatusMessage") or ""
            return f"Feishu/Lark error (code={feishu_code}): {msg}"

        # DingTalk: "errcode" field
        dingtalk_code = data.get("errcode")
        if dingtalk_code is not None and dingtalk_code != 0:
            msg = data.get("errmsg") or ""
            return f"DingTalk error (errcode={dingtalk_code}): {msg}"

        # Slack/Discord: "ok" field
        if data.get("ok") is False:
            error = data.get("error") or ""
            return f"Slack/Discord error: {error}"

        return None

    def _handle_response_status(self, response: httpx.Response, safe_url: str) -> None:
        """Log and display HTTP response status by category.

        Even 2xx responses may contain platform-specific error codes
        in the JSON body (e.g. Feishu code=19001, DingTalk errcode=400,
        Slack ok=false).
        """
        status = response.status_code
        body = response.text[:500]

        if 200 <= status < 300:
            error_hint = self._check_body_error_code(body)
            if error_hint:
                logger.warning(
                    "Webhook 2xx but body contains error: URL=%s, status=%d, body=%s",
                    safe_url, status, body,
                )
                self.console.print(
                    f"[yellow]Webhook response (status={status}): {body}[/yellow]\n"
                    f"[yellow]{error_hint}[/yellow]"
                )
            else:
                logger.info("Webhook sent OK. URL: %s, body: %s", safe_url, body)
                self.console.print(
                    f"[green]Webhook response (status={status}): {body}[/green]"
                )
            return

        if 300 <= status < 400:
            location = response.headers.get("location", "")
            self.console.print(
                f"[yellow]Webhook received redirect (status={status})[/yellow]"
            )
            logger.warning(
                "Webhook redirect: URL=%s, status=%d, location=%s",
                safe_url, status, location,
            )
        elif 400 <= status < 500:
            self.console.print(
                f"[red]Webhook client error (status={status}): {response.text[:500]}[/red]"
            )
            logger.error(
                "Webhook client error: URL=%s, status=%d, body=%s",
                safe_url, status, response.text[:500],
            )
        elif 500 <= status < 600:
            self.console.print(
                f"[red]Webhook server error (status={status}): {response.text[:500]}[/red]"
            )
            logger.error(
                "Webhook server error: URL=%s, status=%d, body=%s",
                safe_url, status, response.text[:500],
            )
        else:
            self.console.print(
                f"[red]Webhook unexpected status={status}: {response.text[:500]}[/red]"
            )
            logger.error("Webhook unexpected status: URL=%s, status=%d", safe_url, status)

    async def send_daily_summary(
        self,
        summary: str,
        important_items: List[ContentItem],
        all_items_count: int,
        date: str,
        lang: str,
        summarizer: DailySummarizer,
    ) -> None:
        """Send daily summary webhook notification.

        Handles language filtering, delivery mode (summary vs summary_and_items),
        and variable construction internally.

        Args:
            summary: Full markdown summary text
            important_items: List of important content items
            all_items_count: Total number of items fetched
            date: Date string (YYYY-MM-DD)
            lang: Language code ("en" or "zh")
            summarizer: DailySummarizer instance for generating webhook overviews
        """
        messages = self.build_daily_summary_messages(
            summary=summary,
            important_items=important_items,
            all_items_count=all_items_count,
            date=date,
            lang=lang,
            summarizer=summarizer,
        )
        if not messages:
            self.console.print(
                f"🔕 Skipping {lang.upper()} webhook notification "
                f"(filtered by webhook.languages)"
            )
            return

        self.console.print(f"🔔 Sending {lang.upper()} webhook notification...")
        for message in messages:
            await self.notify(message)

    async def send_failure(
        self,
        date: str,
        error_message: str,
    ) -> None:
        """Send webhook notification when the pipeline fails.

        Args:
            date: Date string (YYYY-MM-DD)
            error_message: Description of the failure
        """
        self.console.print("🔔 Sending webhook failure notification...")
        await self.notify(
            {
                "date": date,
                "language": "",
                "important_items": 0,
                "all_items": 0,
                "result": "failed",
                "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
                "message_title": "Horizon generation failed",
                "message_kind": "failure",
                "summary": f"generation failed: {error_message}",
            }
        )
