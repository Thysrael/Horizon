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


def test_check_subscriptions_skips_imap_when_disabled(monkeypatch):
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setattr("src.services.email.imaplib.IMAP4_SSL", FakeIMAP)
    FakeIMAP.instances = []

    config = _email_config(imap_enabled=False)
    manager = EmailManager(config)

    manager.check_subscriptions(storage_manager=object())

    assert FakeIMAP.instances == []
