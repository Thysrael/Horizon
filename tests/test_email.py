import base64
import imaplib
from email.mime.multipart import MIMEMultipart
from unittest.mock import Mock

import pytest

from src.models import EmailConfig
from src.services.email import EmailManager
from src.storage.manager import StorageManager


class FakeSMTP:
    instances = []

    def __init__(self, server, port, **kwargs):
        self.server = server
        self.port = port
        self.kwargs = kwargs
        self.login_calls = []
        self.messages = []
        self.ehlo_calls = 0
        self.starttls_calls = []
        self.closed = False
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def login(self, username, password):
        self.login_calls.append((username, password))

    def send_message(self, message):
        self.messages.append(message)

    def ehlo(self):
        self.ehlo_calls += 1

    def starttls(self, **kwargs):
        self.starttls_calls.append(kwargs)

    def close(self):
        self.closed = True


class FakeIMAP:
    instances = []

    def __init__(self, server, port):
        FakeIMAP.instances.append((server, port))


def _email_config(**overrides):
    data = {
        "enabled": True,
        "smtp_server": "smtp.example.com",
        "smtp_port": 465,
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "email_address": "noreply@example.com",
        "password_env": "EMAIL_PASSWORD",
    }
    data.update(overrides)
    return EmailConfig(**data)


def test_send_daily_summary_uses_smtp_username_when_configured(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.smtplib.SMTP_SSL", FakeSMTP)
    FakeSMTP.instances = []

    config = _email_config(smtp_username="resend")
    manager = EmailManager(config)

    manager.send_daily_summary("# Hello", "Daily", ["user@example.com"])

    smtp = FakeSMTP.instances[0]
    assert smtp.login_calls == [("resend", "secret")]
    assert len(smtp.messages) == 1
    assert isinstance(smtp.messages[0], MIMEMultipart)
    assert smtp.messages[0]["From"] == "Horizon Daily <noreply@example.com>"
    assert smtp.messages[0]["To"] == "user@example.com"


def test_send_daily_summary_falls_back_to_email_address_for_smtp_login(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.smtplib.SMTP_SSL", FakeSMTP)
    FakeSMTP.instances = []

    config = _email_config()
    manager = EmailManager(config)

    manager.send_daily_summary("# Hello", "Daily", ["user@example.com"])

    assert FakeSMTP.instances[0].login_calls == [("noreply@example.com", "secret")]


def test_open_smtp_uses_starttls_outside_implicit_tls_port(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.smtplib.SMTP", FakeSMTP)
    FakeSMTP.instances = []

    server = EmailManager(_email_config(smtp_port=587))._open_smtp()

    assert server is FakeSMTP.instances[0]
    assert server.ehlo_calls == 2
    assert len(server.starttls_calls) == 1
    assert "context" in server.starttls_calls[0]


def test_open_smtp_closes_connection_when_starttls_fails(monkeypatch):
    class FailingStartTLS(FakeSMTP):
        def starttls(self, **kwargs):
            raise RuntimeError("TLS unavailable")

    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.smtplib.SMTP", FailingStartTLS)
    FakeSMTP.instances = []

    with pytest.raises(RuntimeError, match="TLS unavailable"):
        EmailManager(_email_config(smtp_port=587))._open_smtp()

    assert FakeSMTP.instances[0].closed is True


def test_send_daily_summary_escapes_raw_html(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.smtplib.SMTP_SSL", FakeSMTP)
    FakeSMTP.instances = []

    manager = EmailManager(_email_config())

    manager.send_daily_summary(
        "# Hello\n\n<img src=x onerror=alert(1)>", "Daily", ["user@example.com"]
    )

    html_part = FakeSMTP.instances[0].messages[0].get_payload()[1]
    html_body = html_part.get_payload(decode=True).decode()
    assert "<h1>Hello</h1>" in html_body
    assert "<img src=x" not in html_body
    assert "&lt;img src=x" in html_body


def test_send_daily_summary_cleans_app_generated_markdown_html(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.smtplib.SMTP_SSL", FakeSMTP)
    FakeSMTP.instances = []

    manager = EmailManager(_email_config())
    summary = """# Daily

<a id="item-1"></a>
## Item

<details><summary>参考链接</summary>
<ul>
<li><a href="https://example.com/a">Example A</a></li>
<li><a href="https://example.com/b">Example B</a></li>
</ul>
</details>
"""

    manager.send_daily_summary(summary, "Daily", ["user@example.com"])

    message = FakeSMTP.instances[0].messages[0]
    text_body = message.get_payload()[0].get_payload(decode=True).decode()
    html_body = message.get_payload()[1].get_payload(decode=True).decode()

    assert '<a id="item-1"></a>' not in text_body
    assert "<details>" not in text_body
    assert "<summary>" not in text_body
    assert "**参考链接**" in text_body
    assert "- [Example A](https://example.com/a)" in text_body

    assert '&lt;a id="item-1"&gt;&lt;/a&gt;' not in html_body
    assert "&lt;details&gt;" not in html_body
    assert "&lt;summary&gt;" not in html_body
    assert "<strong>参考链接</strong>" in html_body
    assert '<a href="https://example.com/a">Example A</a>' in html_body
    assert '<a href="https://example.com/b">Example B</a>' in html_body


def test_send_daily_summary_does_not_link_unsafe_details_href(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.smtplib.SMTP_SSL", FakeSMTP)
    FakeSMTP.instances = []

    manager = EmailManager(_email_config())
    summary = """# Daily

<details><summary>References</summary>
<ul>
<li><a href="javascript:alert(1)">click [me](https://evil.example)</a></li>
</ul>
</details>
"""

    manager.send_daily_summary(summary, "Daily", ["user@example.com"])

    message = FakeSMTP.instances[0].messages[0]
    text_body = message.get_payload()[0].get_payload(decode=True).decode()
    html_body = message.get_payload()[1].get_payload(decode=True).decode()

    assert 'href="javascript:alert(1)"' not in html_body
    assert "[click](javascript:alert(1))" not in text_body
    assert "- click \\[me\\]\\(https://evil.example\\)" in text_body
    assert "click [me](https://evil.example)" in html_body


def test_check_subscriptions_skips_imap_when_disabled(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.imaplib.IMAP4_SSL", FakeIMAP)
    FakeIMAP.instances = []

    config = _email_config(imap_enabled=False)
    manager = EmailManager(config)

    manager.check_subscriptions(storage_manager=object())

    assert FakeIMAP.instances == []


@pytest.mark.parametrize("include_subscription", [False, True])
def test_check_subscriptions_handles_unsubscribe_before_fetch_marks_seen(
    monkeypatch: pytest.MonkeyPatch, include_subscription: bool
) -> None:
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    subjects = {b"1": ("UNSUBSCRIBE", "leaving@example.com")}
    if include_subscription:
        subjects[b"2"] = ("SUBSCRIBE", "joining@example.com")
    seen: set[bytes] = set()

    def search(charset: None, criteria: str) -> tuple[str, list[bytes]]:
        keyword = criteria.split('"')[1]
        ids = [
            message_id
            for message_id, (subject, _) in subjects.items()
            if message_id not in seen and keyword in subject
        ]
        return "OK", [b" ".join(ids)]

    def fetch(message_id: bytes, query: str) -> tuple[str, list[tuple[bytes, bytes]]]:
        if query == "(RFC822)":
            seen.add(message_id)
        subject, sender = subjects[message_id]
        message = f"From: {sender}\r\nSubject: {subject}\r\n\r\n".encode()
        return "OK", [(message_id, message)]

    mail = Mock(spec=imaplib.IMAP4_SSL)
    mail.search.side_effect = search
    mail.fetch.side_effect = fetch
    monkeypatch.setattr("src.services.email.imaplib.IMAP4_SSL", Mock(return_value=mail))
    storage = Mock(spec=StorageManager)
    storage.load_subscribers.return_value = ["leaving@example.com"]
    manager = EmailManager(_email_config())
    reply = Mock()
    monkeypatch.setattr(manager, "_send_reply", reply)

    manager.check_subscriptions(storage)
    manager.check_subscriptions(storage)

    storage.remove_subscriber.assert_called_once_with("leaving@example.com")
    if include_subscription:
        storage.add_subscriber.assert_called_once_with("joining@example.com")
    else:
        storage.add_subscriber.assert_not_called()
    assert reply.call_count == 1 + int(include_subscription)


@pytest.mark.parametrize("keyword", ["SUBSCRIBE", "UNSUBSCRIBE"])
@pytest.mark.parametrize(
    ("subject", "matches"),
    [
        ("{keyword}", True),
        ("=?utf-8?q?{keyword}?=", True),
        ("=?utf-8?b?{encoded_keyword}?=", True),
        ("=?utf-8?q?{first_half}?=\r\n =?utf-8?q?{second_half}?=", True),
        ("Re: {keyword}", False),
        ("=?utf-8?q?Re=3A_{keyword}?=", False),
    ],
)
def test_check_subscriptions_matches_decoded_subject(
    monkeypatch: pytest.MonkeyPatch, keyword: str, subject: str, matches: bool
) -> None:
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    encoded_keyword = base64.b64encode(keyword.encode()).decode()
    midpoint = len(keyword) // 2
    subject = subject.format(
        keyword=keyword,
        encoded_keyword=encoded_keyword,
        first_half=keyword[:midpoint],
        second_half=keyword[midpoint:],
    )
    raw_message = f"From: user@example.com\r\nSubject: {subject}\r\n\r\n".encode()
    mail = Mock(spec=imaplib.IMAP4_SSL)
    mail.search.side_effect = [
        ("OK", [b"1" if keyword == "SUBSCRIBE" else b""]),
        ("OK", [b"1" if keyword == "UNSUBSCRIBE" else b""]),
    ]
    mail.fetch.return_value = ("OK", [(b"1 (RFC822)", raw_message)])
    monkeypatch.setattr("src.services.email.imaplib.IMAP4_SSL", Mock(return_value=mail))
    storage = Mock(spec=StorageManager)
    storage.load_subscribers.return_value = (
        [] if keyword == "SUBSCRIBE" else ["user@example.com"]
    )
    manager = EmailManager(_email_config())
    monkeypatch.setattr(manager, "_send_reply", Mock())

    manager.check_subscriptions(storage)

    operation = (
        storage.add_subscriber if keyword == "SUBSCRIBE" else storage.remove_subscriber
    )
    if matches:
        operation.assert_called_once_with("user@example.com")
    else:
        operation.assert_not_called()
