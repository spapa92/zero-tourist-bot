import datetime as dt
import hashlib
import hmac

from app.whatsapp.client import WhatsAppClient, is_window_open
from app.whatsapp.webhook import verify_signature


def test_verify_signature_valid():
    secret = "s3cr3t"
    body = b'{"hello": "world"}'
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, secret, sig) is True


def test_verify_signature_invalid():
    secret = "s3cr3t"
    body = b'{"hello": "world"}'
    assert verify_signature(body, secret, "sha256=bad") is False


def test_verify_signature_empty_secret():
    assert verify_signature(b"body", "", "sha256=abc") is False


def test_window_open_within_24h():
    now = dt.datetime(2026, 8, 26, 12, 0, tzinfo=dt.timezone.utc)
    last = now - dt.timedelta(hours=1)
    assert is_window_open(last, now) is True


def test_window_closed_after_24h():
    now = dt.datetime(2026, 8, 26, 12, 0, tzinfo=dt.timezone.utc)
    last = now - dt.timedelta(hours=25)
    assert is_window_open(last, now) is False


def test_window_none_closed():
    assert is_window_open(None) is False


class _RecordingClient(WhatsAppClient):
    def __init__(self) -> None:
        self.texts: list[tuple] = []
        self.templates: list[tuple] = []

    def send_text(self, to, text):
        self.texts.append((to, text))
        return {"ok": True}

    def send_template(self, to, template_name, components=None):
        self.templates.append((to, template_name))
        return {"ok": True}


def test_send_reply_free_form_when_window_open():
    client = _RecordingClient()
    now = dt.datetime.now(dt.timezone.utc)
    client.send_reply("123", "ciao", now - dt.timedelta(hours=1))
    assert client.texts and not client.templates


def test_send_reply_template_when_window_closed():
    client = _RecordingClient()
    now = dt.datetime.now(dt.timezone.utc)
    client.send_reply("123", "ciao", now - dt.timedelta(hours=25))
    assert client.templates and not client.texts
    assert client.templates[0][1] == "reopener"
