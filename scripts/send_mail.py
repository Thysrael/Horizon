"""Horizon 每日简报的邮件通知发送器。

由 scripts/run_daily.ps1 调用（在日报生成之后）。

为什么用 Python 而不是 PowerShell 的 System.Net.Mail.SmtpClient：
在 Windows PowerShell 5.1 下，SmtpClient 连接 smtp.qiye.aliyun.com:465 会在
认证阶段被服务器断开（net_io_connectionclosed / SmtpException GeneralFailure），
而同样的凭据用 Python 的 smtplib 认证与发送均正常。

SMTP 配置从 .env 读取（该文件已被 .gitignore 忽略）：
    SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD / SMTP_TO / SMTP_SENDER_NAME

用法：
    python scripts/send_mail.py --subject "..." --body body.txt --markdown report.md
退出码：0 = 发送成功，1 = 发送失败（错误信息打印到 stdout/stderr）。
"""

from __future__ import annotations

import argparse
import html as html_mod
import re
import smtplib
import email.utils as email_utils
from email.policy import SMTP as SMTP_POLICY
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

# ----------------------------------------------------------------------------------
# Markdown -> HTML 渲染
#
# 只针对 Horizon 日报的结构做定向解析，而不是通用 Markdown：
#   # 标题 / > 副标题 / **分组名** / N. [条目](#anchor) ⭐️ 8.0/10
#   ## 章节 / ### [条目](url) ⭐️ 8.0/10 / <a id="..."> / 正文段
#   来源行（source · author · date · [社区讨论](url)）
#   **「小节名」** 内容 / <details>参考链接</details> / **标签**: `#A`, `#B`
#
# 邮件 HTML 必须全部使用 inline style（Outlook 的 Word 渲染引擎不认 <style> 块），
# <details>/<summary> 也要展开成常驻区块——Outlook 根本不支持这两个标签。
# ----------------------------------------------------------------------------------

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")
_TAG_RE = re.compile(r"`(#[^`]+)`")

_RE_ANCHOR = re.compile(r'^<a id="([^"]+)"></a>\s*$')
# Whole line made of HTML tags only -> not human readable, drop it.
_RE_TAG_LINE = re.compile(r'^(?:</?[a-zA-Z][a-zA-Z0-9]*\b[^>]*>\s*)+$')
_RE_H3 = re.compile(r"^###\s+\[(.+?)\]\((.+?)\)\s*(.*)$")
_RE_H2 = re.compile(r"^##\s+(.+?)\s*$")
_RE_H1 = re.compile(r"^#\s+(.+?)\s*$")
_RE_QUOTE = re.compile(r"^>\s*(.+?)\s*$")
_RE_HR = re.compile(r"^-{3,}\s*$")
_RE_BOLD_ONLY = re.compile(r"^\*\*(.+?)\*\*\s*$")
_RE_TOC = re.compile(r"^(\d+)\.\s+\[(.+?)\]\((.+?)\)\s*(.*)$")
_RE_LABELLED = re.compile(r"^\*\*(.+?)\*\*[:：]?\s*(.*)$")
_RE_SCORE = re.compile(r"⭐️?\s*([\d.]+)\s*/\s*10")
_RE_META = re.compile(r"^[a-z0-9_]+\s·\s")

_MAIL_FONT = (
    "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',"
    "'Microsoft YaHei','Hiragino Sans GB',Roboto,Helvetica,Arial,sans-serif"
)


def _esc(text: str) -> str:
    return html_mod.escape(text, quote=False)


def _esc_attr(text: str) -> str:
    return html_mod.escape(text, quote=True)


def _inline(text: str) -> str:
    """行内 Markdown -> HTML。先转义原文，再插入标签，避免标签被转义掉。"""
    out: list[str] = []
    pos = 0
    for match in _LINK_RE.finditer(text):
        out.append(_esc(text[pos : match.start()]))
        out.append(
            f'<a href="{_esc_attr(match.group(2))}" '
            f'style="color:#1d4ed8;text-decoration:none">{_esc(match.group(1))}</a>'
        )
        pos = match.end()
    out.append(_esc(text[pos:]))
    rendered = "".join(out)
    # 下面两处作用在"已转义"的文本上，替换时不能再转义，否则 &amp; 会变成 &amp;amp;
    rendered = _BOLD_RE.sub(
        lambda m: f'<strong style="color:#0f172a;font-weight:600">{m.group(1)}</strong>',
        rendered,
    )
    rendered = _CODE_RE.sub(
        lambda m: (
            f'<code style="background:#f1f5f9;color:#334155;padding:1px 4px;'
            f'border-radius:3px;font-size:13px">{m.group(1)}</code>'
        ),
        rendered,
    )
    return rendered


def _score_badge(text: str) -> str:
    """把 '⭐️ 8.0/10' 渲染成评分徽章。"""
    match = _RE_SCORE.search(text or "")
    if not match:
        return ""
    score = float(match.group(1))
    if score >= 8:
        bg, fg = "#fef3c7", "#92400e"
    elif score >= 7:
        bg, fg = "#e0f2fe", "#075985"
    else:
        bg, fg = "#f1f5f9", "#475569"
    return (
        f'<span style="display:inline-block;background:{bg};color:{fg};font-size:12px;'
        f'font-weight:700;padding:2px 8px;border-radius:10px;white-space:nowrap">'
        f"{score:.1f}/10</span>"
    )


def _collect_anchors(lines: list[str]) -> dict[str, str]:
    """'<a id="item-x"></a>' -> 该条目的原始 URL（目录里的 #锚点 要还原成真实链接）。"""
    anchors: dict[str, str] = {}
    for index, line in enumerate(lines):
        match = _RE_ANCHOR.match(line.strip())
        if not match:
            continue
        for follow in lines[index + 1 : index + 4]:
            h3 = _RE_H3.match(follow.strip())
            if h3:
                anchors[match.group(1)] = h3.group(2)
                break
    return anchors


def _render_references(block: list[str]) -> str:
    """<details> 参考链接 -> 常驻区块（Outlook 不支持 details）。"""
    title = "参考链接"
    items: list[str] = []
    for line in block:
        stripped = line.strip()
        if stripped.startswith("<summary>"):
            title = re.sub(r"</?summary>", "", stripped).strip() or title
        elif stripped.startswith("<li>"):
            link = re.search(r'href="([^"]+)"[^>]*>(.*?)</a>', stripped)
            if link:
                label = re.sub(r"<[^>]+>", "", link.group(2))
                items.append(
                    '<li style="font-size:13px;line-height:1.75;margin:0">'
                    f'<a href="{_esc_attr(link.group(1))}" '
                    f'style="color:#1d4ed8;text-decoration:none">{_esc(label)}</a></li>'
                )
    inner = "".join(items) or '<li style="font-size:13px;color:#64748b">（无）</li>'
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="margin:10px 0 4px 0"><tr><td style="padding:10px 12px;'
        'background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px">'
        f'<div style="font-size:12px;font-weight:700;color:#475569;margin-bottom:6px">'
        f"{_esc(title)}</div>"
        f'<ul style="margin:0;padding-left:18px">{inner}</ul>'
        "</td></tr></table>"
    )


def _split_details(lines: list[str]) -> tuple[list[str], list[str]]:
    """把 <details> 块抽成占位符，返回 (替换后的行, 各块的 HTML)。"""
    normalized: list[str] = []
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("<details>"):
            end = index
            while end < len(lines) and "</details>" not in lines[end]:
                end += 1
            token = f"\x00REF{len(blocks)}\x00"
            blocks.append(_render_references(lines[index : end + 1]))
            normalized.append(token)
            index = end + 1
            continue
        normalized.append(lines[index])
        index += 1
    return normalized, blocks


def render_digest_html(markdown: str) -> str:
    """把日报 Markdown 渲染成一封邮件用的 HTML 正文。"""
    lines = markdown.splitlines()
    anchors = _collect_anchors(lines)
    normalized, blocks = _split_details(lines)

    parts: list[str] = []
    for raw in normalized:
        stripped = raw.strip()
        if not stripped:
            continue
        if _RE_ANCHOR.match(stripped) or _RE_TAG_LINE.match(stripped):
            # The TOC links already point at the real article URLs, so the
            # anchor markup carries no jump target. Dropping the line keeps
            # raw tags from being rendered as visible text.
            continue

        if stripped.startswith("\x00REF"):
            parts.append(blocks[int(stripped[4:-1])])
            continue

        h3 = _RE_H3.match(stripped)
        if h3:
            title, url, tail = h3.groups()
            parts.append(
                '<h3 style="margin:20px 0 8px 0;font-size:17px;line-height:1.45;'
                'font-weight:700;color:#0f172a">'
                f'<a href="{_esc_attr(url)}" style="color:#0f172a;text-decoration:none">'
                f"{_esc(title)}</a> {_score_badge(tail)}</h3>"
            )
            continue

        toc = _RE_TOC.match(stripped)
        if toc:
            number, title, target, tail = toc.groups()
            url = anchors.get(target.lstrip("#"), target)
            parts.append(
                '<div style="font-size:14px;line-height:1.9;color:#1f2937;'
                'margin:0 0 0 0;padding-left:2px">'
                f'<span style="color:#94a3b8;margin-right:4px">{number}.</span>'
                f'<a href="{_esc_attr(url)}" style="color:#1f2937;text-decoration:none">'
                f"{_esc(title)}</a> {_score_badge(tail)}</div>"
            )
            continue

        h1 = _RE_H1.match(stripped)
        if h1:
            parts.append(
                '<h1 style="margin:0 0 6px 0;font-size:22px;line-height:1.3;'
                f'font-weight:700;color:#0f172a">{_esc(h1.group(1))}</h1>'
            )
            continue

        h2 = _RE_H2.match(stripped)
        if h2:
            parts.append(
                '<h2 style="margin:26px 0 10px 0;font-size:16px;line-height:1.4;'
                'font-weight:700;color:#0f172a;padding-bottom:6px;'
                'border-bottom:2px solid #e2e8f0">'
                f"{_esc(h2.group(1))}</h2>"
            )
            continue

        quote = _RE_QUOTE.match(stripped)
        if quote:
            parts.append(
                '<p style="margin:0 0 14px 0;font-size:14px;color:#64748b">'
                f"{_inline(quote.group(1))}</p>"
            )
            continue

        if _RE_HR.match(stripped):
            parts.append(
                '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
                'style="margin:16px 0"><tr><td style="height:1px;background:#e2e8f0;'
                'font-size:0;line-height:0">&nbsp;</td></tr></table>'
            )
            continue

        bold_only = _RE_BOLD_ONLY.match(stripped)
        if bold_only:
            parts.append(
                '<h2 style="margin:18px 0 8px 0;font-size:15px;font-weight:700;'
                f'color:#334155">{_esc(bold_only.group(1))}</h2>'
            )
            continue

        labelled = _RE_LABELLED.match(stripped)
        if labelled:
            label, rest = labelled.groups()
            if label.startswith("「"):
                parts.append(
                    '<p style="margin:8px 0;padding:2px 0 2px 12px;'
                    'border-left:3px solid #cbd5e1;font-size:14px;line-height:1.8;'
                    'color:#334155">'
                    f'<strong style="color:#0f172a;font-weight:600">{_esc(label)}</strong> '
                    f"{_inline(rest)}</p>"
                )
            else:
                chips = "".join(
                    '<span style="display:inline-block;background:#f1f5f9;color:#475569;'
                    f'font-size:12px;padding:2px 7px;border-radius:3px;margin-right:4px;'
                    f'margin-top:3px">{_esc(tag)}</span>'
                    for tag in _TAG_RE.findall(rest)
                )
                plain = _TAG_RE.sub("", rest).strip().strip(",").strip()
                parts.append(
                    '<div style="margin:8px 0 4px 0">'
                    f'<span style="font-size:12px;color:#94a3b8;margin-right:6px">'
                    f"{_esc(label)}</span>{chips}"
                    + (f'<span style="font-size:12px;color:#94a3b8">{_esc(plain)}</span>' if plain else "")
                    + "</div>"
                )
            continue

        if _RE_META.match(stripped):
            parts.append(
                '<p style="margin:2px 0 10px 0;font-size:12px;color:#94a3b8">'
                f"{_inline(stripped)}</p>"
            )
            continue

        parts.append(
            '<p style="margin:8px 0;font-size:14px;line-height:1.85;color:#1f2937">'
            f"{_inline(stripped)}</p>"
        )

    body = "".join(parts)
    return (
        "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Horizon 每日速递</title></head>"
        f'<body style="margin:0;padding:0;background:#f1f5f9;'
        f'font-family:{_MAIL_FONT};-webkit-text-size-adjust:100%">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="background:#f1f5f9"><tr><td align="center" style="padding:20px 12px">'
        '<table role="presentation" width="620" cellspacing="0" cellpadding="0" '
        'style="width:620px;max-width:100%;background:#ffffff;border-radius:10px;'
        'border:1px solid #e2e8f0">'
        '<tr><td style="padding:24px 26px 20px 26px">'
        f"{body}"
        '</td></tr><tr><td style="padding:0 26px 22px 26px">'
        '<p style="margin:0;font-size:12px;color:#94a3b8">'
        "由 Horizon 自动生成 · 完整 Markdown 原文见附件</p>"
        "</td></tr></table>"
        "</td></tr></table></body></html>"
    )


# ----------------------------------------------------------------------------------
# 发送
# ----------------------------------------------------------------------------------


def load_env(path: Path) -> dict[str, str]:
    """解析 .env：忽略空行与 # 开头的注释行，值可被单/双引号包裹。"""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        env[key.strip()] = value
    return env


def markdown_to_plain(markdown: str) -> str:
    """Strip Markdown/HTML decoration so the digest reads as plain text.

    The plain-text part must carry roughly the same content as the HTML part.
    A tiny text body next to a huge HTML body is a classic spam signal
    (low text-to-HTML ratio), so we keep the full digest in both parts.
    """
    anchors = _collect_anchors(markdown.splitlines())

    def _anchor_url(match: re.Match[str]) -> str:
        target = match.group(2)
        if target.startswith("#"):
            target = anchors.get(target.lstrip("#"), target)
        return f"{match.group(1)} ({target})"

    text = re.sub(r"<a\s+id=\"[^\"]*\"\s*>\s*</a>", "", markdown)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _anchor_url, text)
    text = re.sub(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', r"\2 (\1)", text, flags=re.S)
    text = re.sub(r"</?details>", "", text)
    text = re.sub(r"<summary>(.*?)</summary>", r"\1", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_mod.unescape(text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^>\s*", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Send the Horizon daily briefing by email.")
    parser.add_argument("--env", required=True, help="path to the .env file holding SMTP settings")
    parser.add_argument("--subject", required=True, help="mail subject")
    parser.add_argument("--body", required=True, help="path to a UTF-8 file holding the plain-text body")
    parser.add_argument("--markdown", default="", help="path to the digest Markdown, rendered as the HTML body")
    parser.add_argument("--to", default="", help="comma separated recipients (defaults to SMTP_TO)")
    parser.add_argument("--attach", action="append", default=[], help="attachment path (repeatable)")
    parser.add_argument("--from-name", default="", help="display name of the sender")
    args = parser.parse_args()

    env = load_env(Path(args.env))
    host = env.get("SMTP_HOST", "")
    user = env.get("SMTP_USERNAME", "")
    password = env.get("SMTP_PASSWORD", "")
    recipients = args.to.strip() or env.get("SMTP_TO", "")
    sender_name = args.from_name.strip() or env.get("SMTP_SENDER_NAME", "") or "Horizon Daily Briefing"

    missing = [
        name
        for name, value in (
            ("SMTP_HOST", host),
            ("SMTP_USERNAME", user),
            ("SMTP_PASSWORD", password),
            ("SMTP_TO", recipients),
        )
        if not value
    ]
    if missing:
        print(f"send_mail: missing SMTP settings: {', '.join(missing)}", file=sys.stderr)
        return 1

    try:
        port = int(env.get("SMTP_PORT", "465"))
    except ValueError:
        port = 465

    dkim_selector = env.get("DKIM_SELECTOR", "").strip()
    dkim_domain = env.get("DKIM_DOMAIN", "").strip() or "weante.net"
    dkim_key_rel = env.get("DKIM_PRIVATE_KEY_PATH", "").strip() or ".local-backup/dkim_private.pem"
    dkim_privkey_path = Path(dkim_key_rel)
    if not dkim_privkey_path.is_absolute():
        # Resolve relative to the working directory first (the daily script runs
        # from the Horizon root), then next to the .env file, then its parent.
        candidates = [
            Path.cwd() / dkim_key_rel,
            Path(args.env).resolve().parent / dkim_key_rel,
            Path(args.env).resolve().parent.parent / dkim_key_rel,
        ]
        dkim_privkey_path = next(
            (c for c in candidates if c.exists()), candidates[0]
        )

    body_path = Path(args.body)
    body = body_path.read_text(encoding="utf-8") if body_path.exists() else ""

    message = EmailMessage()
    message["From"] = f"{sender_name} <{user}>"
    message["To"] = recipients
    message["Subject"] = args.subject
    # RFC 5322 makes Date and Message-ID mandatory. Mail that arrives without
    # them looks machine-generated to reputation filters and gets silently
    # dropped by some providers (Hotmail in particular).
    message["Date"] = email_utils.formatdate(localtime=True)
    message["Message-ID"] = email_utils.make_msgid(domain="weante.net")

    html_body = ""
    plain_body = body
    if args.markdown:
        markdown_path = Path(args.markdown)
        if markdown_path.exists():
            markdown_text = markdown_path.read_text(encoding="utf-8")
            html_body = render_digest_html(markdown_text)
            # Keep the plain-text part as rich as the HTML part: a 1 KB text
            # body next to a 70 KB HTML body is what mail filters score down.
            header = body.split("本期条目")[0].rstrip() if "本期条目" in body else body.rstrip()
            plain_body = (
                f"{header}\n\n{markdown_to_plain(markdown_text)}\n\n"
                "完整日报见附件（Markdown）。\n"
            )

    if html_body:
        # multipart/alternative：纯文本兜底 + HTML 正文，Outlook 优先显示 HTML。
        message.set_content(plain_body)
        message.add_alternative(html_body, subtype="html")
    else:
        message.set_content(plain_body)

    attached = 0
    for raw_path in args.attach:
        path = Path(raw_path)
        if not path.exists():
            print(f"send_mail: attachment missing, skipped: {path}", file=sys.stderr)
            continue
        message.add_attachment(
            path.read_text(encoding="utf-8"),
            subtype="markdown",
            filename=path.name,
        )
        attached += 1

    # Serialize with CRLF line endings so the DKIM signature survives the
    # SMTP transfer (smtplib only rewrites bare LFs).
    raw = message.as_bytes(policy=SMTP_POLICY)

    dkim_state = "off"
    if dkim_selector and dkim_privkey_path and dkim_privkey_path.exists():
        try:
            import dkim

            # dkim.sign() returns only the DKIM-Signature header field
            # (terminated by CRLF); the message body has to be re-attached.
            signature = dkim.sign(
                raw,
                dkim_selector.encode("ascii"),
                dkim_domain.encode("ascii"),
                dkim_privkey_path.read_bytes(),
                canonicalize=(b"relaxed", b"relaxed"),
            )
            raw = signature + raw
            dkim_state = f"signed:{dkim_selector}._domainkey.{dkim_domain}"
        except Exception as exc:  # noqa: BLE001 - never block delivery on signing
            print(f"send_mail: DKIM signing failed, sending unsigned: {exc}", file=sys.stderr)
            dkim_state = "failed"
    elif dkim_selector:
        print(f"send_mail: DKIM key not found at {dkim_privkey_path}, sending unsigned", file=sys.stderr)
        dkim_state = "missing-key"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=60) as server:
            server.login(user, password)
            server.sendmail(user, [r.strip() for r in recipients.split(",") if r.strip()], raw)
    except Exception as exc:  # noqa: BLE001 - report every failure to the caller
        print(f"send_mail: send failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(
        f"send_mail: sent to {recipients} (attachments={attached}, "
        f"html={'yes' if html_body else 'no'}, dkim={dkim_state})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
