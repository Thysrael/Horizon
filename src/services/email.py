"""Email service for handling subscriptions and sending summaries."""

import email
import html
import imaplib
import logging
import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from typing import List

try:
    import markdown
except ImportError:
    markdown = None

from rich.console import Console

from ..ai.markdown_utils import clean_app_summary_markdown
from ..models import EmailConfig

logger = logging.getLogger(__name__)

# The summarizer HTML-escapes untrusted text and then Markdown-escapes it,
# which turns "&#x27;" into "&\#x27;". These helpers undo that once for email.
_ESCAPED_ENTITY_RE = re.compile(r"&\\#(x?[0-9A-Fa-f]+);")
_CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1", re.DOTALL)
_MARKDOWN_BACKSLASH_RE = re.compile(r"\\([\\`*_{}\[\]()<>#!|+.-])")
_LIST_ITEM = r"[ \t]*(?:\d+[.)]|[-*+])[ \t]"
_LIST_AFTER_TEXT_RE = re.compile(rf"(?m)^((?!{_LIST_ITEM}).*\S.*)\n(?={_LIST_ITEM})")


def _escape_email_text(value: str) -> str:
    """Block raw HTML without escaping the summarizer's entities a second time.

    Escaping < is enough to stop raw HTML. Existing entities such as &#x27;
    are left for Markdown to pass through, and bare & is escaped by Markdown.
    > is left alone so the app's own blockquotes still work; untrusted text
    reaches here as &gt;, so it can't start one. Python-Markdown doesn't treat
    \\| as an escape, so it is unescaped to avoid a stray backslash.
    """
    return value.replace("<", "&lt;").replace("\\|", "|")


def _prepare_email_markdown(value: str) -> str:
    """Make summary Markdown render cleanly, and safely, as email HTML.

    Summary text is already HTML-escaped by the summarizer, so escaping it
    again here showed entities such as &#x27; and &quot; in the email.
    """
    value = _ESCAPED_ENTITY_RE.sub(r"&#\1;", value)
    parts = []
    last = 0
    for match in _CODE_SPAN_RE.finditer(value):
        parts.append(_escape_email_text(value[last : match.start()]))
        # Markdown escapes code span contents itself, and backslashes are
        # literal there, so decode fully and let Markdown do the escaping.
        code = html.unescape(_MARKDOWN_BACKSLASH_RE.sub(r"\1", match.group(2)))
        parts.append(f"`` {code} ``" if "`" in code else f"`{code}`")
        last = match.end()
    parts.append(_escape_email_text(value[last:]))
    # Python-Markdown needs a blank line before a list that follows text.
    return _LIST_AFTER_TEXT_RE.sub(r"\1\n\n", "".join(parts))


class EmailManager:
    """Manages email subscriptions and sending summaries."""

    def __init__(self, config: EmailConfig, console=None):
        self.config = config
        self.pwd = os.getenv(self.config.password_env)
        self.console = console if console is not None else Console(stderr=True)

        if not self.pwd and self.config.enabled:
            logger.warning(
                f"Environment variable {self.config.password_env} not set. Email features may fail."
            )
            self.console.print(
                f"[yellow]Warning: Environment variable {self.config.password_env} not set. Email features may fail.[/yellow]"
            )

    def check_subscriptions(self, storage_manager):
        """Checks inbox for subscription requests and updates subscriber list."""
        if not self.config.enabled or not self.config.imap_enabled:
            return

        try:
            mail = imaplib.IMAP4_SSL(self.config.imap_server, self.config.imap_port)
            mail.login(self.config.email_address, self.pwd)
            mail.select("INBOX")

            keyword = self.config.subscribe_keyword
            search_crit = f'(UNSEEN SUBJECT "{keyword}")'

            status, messages = mail.search(None, search_crit)

            if status == "OK" and messages[0]:
                email_ids = messages[0].split()
                subscribers = storage_manager.load_subscribers()

                for e_id in email_ids:
                    _, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])

                            subject = str(msg.get("Subject") or "").strip()
                            if subject.upper() != keyword.upper():
                                continue

                            sender = msg.get("From")

                            if sender:
                                _, email_addr = parseaddr(sender)
                                if email_addr and "@" in email_addr:
                                    if (
                                        "noreply" in email_addr.lower()
                                        or "no-reply" in email_addr.lower()
                                    ):
                                        continue

                                    if email_addr not in subscribers:
                                        storage_manager.add_subscriber(email_addr)
                                        subscribers = storage_manager.load_subscribers()
                                        self._send_reply(
                                            email_addr,
                                            "Subscribed to Horizon",
                                            "You have been successfully subscribed to Horizon daily summaries.",
                                        )
                                        logger.info(f"Added subscriber: {email_addr}")
                                    else:
                                        logger.info(f"Already subscribed: {email_addr}")

            unsub_keyword = self.config.unsubscribe_keyword
            search_crit_unsub = f'(UNSEEN SUBJECT "{unsub_keyword}")'

            status, messages = mail.search(None, search_crit_unsub)

            if status == "OK" and messages[0]:
                email_ids = messages[0].split()
                subscribers = storage_manager.load_subscribers()

                for e_id in email_ids:
                    _, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])

                            subject = str(msg.get("Subject") or "").strip()
                            if subject.upper() != unsub_keyword.upper():
                                continue

                            sender = msg.get("From")

                            if sender:
                                _, email_addr = parseaddr(sender)
                                if email_addr and "@" in email_addr:
                                    if (
                                        "noreply" in email_addr.lower()
                                        or "no-reply" in email_addr.lower()
                                    ):
                                        continue

                                    if email_addr in subscribers:
                                        storage_manager.remove_subscriber(email_addr)
                                        subscribers = storage_manager.load_subscribers()
                                        self._send_reply(
                                            email_addr,
                                            "Unsubscribed from Horizon",
                                            "You have been successfully unsubscribed from Horizon daily summaries.",
                                        )
                                        logger.info(f"Removed subscriber: {email_addr}")
                                    else:
                                        logger.info(f"Not subscribed: {email_addr}")

            mail.close()
            mail.logout()

        except Exception as e:
            logger.error(f"Error checking subscriptions: {e}")

    def _open_smtp(self) -> smtplib.SMTP:
        """Open an implicit TLS or STARTTLS SMTP connection."""
        context = ssl.create_default_context()
        if self.config.smtp_port == 465:
            return smtplib.SMTP_SSL(
                self.config.smtp_server, self.config.smtp_port, context=context
            )

        server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
        try:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        except Exception:
            server.close()
            raise
        return server

    def send_daily_summary(self, summary_md: str, subject: str, subscribers: List[str]):
        """Sends the daily summary to all subscribers."""
        if not self.config.enabled or not subscribers:
            return

        cleaned_summary = clean_app_summary_markdown(summary_md)
        safe_summary = _prepare_email_markdown(cleaned_summary)
        html_content = (
            markdown.markdown(safe_summary)
            if markdown
            else f"<pre>{safe_summary}</pre>"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                code {{ background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
                pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                blockquote {{ border-left: 4px solid #ddd; padding-left: 15px; color: #777; }}
                .footer {{ margin-top: 40px; font-size: 12px; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
            </style>
        </head>
        <body>
            {html_content}
            <div class="footer">
                <p>Sent by {self.config.sender_name}</p>
                <p>To unsubscribe, please reply with "{self.config.unsubscribe_keyword}"</p>
            </div>
        </body>
        </html>
        """

        try:
            with self._open_smtp() as server:
                server.login(
                    self.config.smtp_username or self.config.email_address, self.pwd
                )

                for subscriber in subscribers:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = (
                        f"{self.config.sender_name} <{self.config.email_address}>"
                    )
                    msg["To"] = subscriber

                    text_part = MIMEText(cleaned_summary, "plain")
                    html_part = MIMEText(html_body, "html")

                    msg.attach(text_part)
                    msg.attach(html_part)

                    try:
                        server.send_message(msg)
                        logger.info(f"Sent summary to {subscriber}")
                    except Exception as e:
                        logger.error(f"Failed to send to {subscriber}: {e}")

        except Exception as e:
            logger.error(f"SMTP Error: {e}")

    def _send_reply(self, to_email: str, subject: str, body: str):
        """Helper to send a simple reply."""
        try:
            with self._open_smtp() as server:
                server.login(
                    self.config.smtp_username or self.config.email_address, self.pwd
                )

                msg = MIMEText(body)
                msg["Subject"] = subject
                msg["From"] = f"{self.config.sender_name} <{self.config.email_address}>"
                msg["To"] = to_email

                server.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send reply to {to_email}: {e}")
