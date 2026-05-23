from email.mime.multipart import MIMEMultipart

from src.models import EmailConfig
from src.services.email import EmailManager


class FakeSMTP:
    instances = []

    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.login_calls = []
        self.messages = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def login(self, username, password):
        self.login_calls.append((username, password))

    def send_message(self, message):
        self.messages.append(message)


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
