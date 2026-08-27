"""Provider Meta: verifica firma webhook e payload della Cloud API."""

import hashlib
import hmac

import httpx
import pytest

from app.whatsapp.client import WhatsAppNotConfigured
from app.whatsapp.providers.meta import MetaWhatsAppClient
from app.whatsapp.webhooks.meta import verify_signature
from tests.helpers import FakeHTTP


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


def _client() -> MetaWhatsAppClient:
    return MetaWhatsAppClient("tok", "111222333")


def test_send_text_payload(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    _client().send_text("393331234567", "ciao")

    call = http.calls[0]
    assert call.url == "https://graph.facebook.com/v21.0/111222333/messages"
    assert call.kwargs["headers"]["Authorization"] == "Bearer tok"
    assert call.kwargs["json"] == {
        "messaging_product": "whatsapp",
        "to": "393331234567",
        "type": "text",
        "text": {"body": "ciao"},
    }


def test_send_template_maps_variables_to_components(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    _client().send_template("393331234567", "reminder_visita", {"2": "18:30", "1": "domani"})

    template = http.calls[0].kwargs["json"]["template"]
    assert template["name"] == "reminder_visita"
    assert template["language"] == {"code": "it"}
    assert template["components"] == [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": "domani"},
                {"type": "text", "text": "18:30"},
            ],
        }
    ]


def test_send_template_without_variables_has_no_components(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    _client().send_template("393331234567", "reopener")

    assert "components" not in http.calls[0].kwargs["json"]["template"]


def test_missing_credentials_raise(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    with pytest.raises(WhatsAppNotConfigured):
        MetaWhatsAppClient("", "").send_text("393331234567", "ciao")
    assert not http.calls


def test_is_configured():
    assert _client().is_configured() is True
    assert MetaWhatsAppClient("tok", "").is_configured() is False
