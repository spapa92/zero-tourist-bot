"""Provider Twilio: normalizzazione indirizzi, payload API e validazione firma."""

import json

import httpx
import pytest

from app.whatsapp.client import TemplateNotConfigured, WhatsAppNotConfigured
from app.whatsapp.providers.twilio import (
    TwilioWhatsAppClient,
    from_whatsapp_address,
    to_whatsapp_address,
)
from app.whatsapp.webhooks.twilio import compute_signature, verify_signature
from tests.helpers import FakeHTTP


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("+393331234567", "whatsapp:+393331234567"),
        ("393331234567", "whatsapp:+393331234567"),
        ("whatsapp:+393331234567", "whatsapp:+393331234567"),
        (" whatsapp:393331234567 ", "whatsapp:+393331234567"),
        ("", ""),
    ],
)
def test_to_whatsapp_address(value, expected):
    assert to_whatsapp_address(value) == expected


def test_from_whatsapp_address_strips_prefix():
    assert from_whatsapp_address("whatsapp:+393331234567") == "+393331234567"
    assert from_whatsapp_address("+393331234567") == "+393331234567"


def _client(**kwargs) -> TwilioWhatsAppClient:
    options = {
        "from_number": "+14155238886",
        "content_sids": {"reopener": "HXreopener"},
    }
    options.update(kwargs)
    return TwilioWhatsAppClient("AC123", "token", **options)


def test_send_text_payload(monkeypatch):
    http = FakeHTTP({"sid": "SM1"})
    monkeypatch.setattr(httpx, "post", http)

    _client().send_text("393331234567", "ciao")

    call = http.calls[0]
    assert call.url == "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages.json"
    assert call.kwargs["auth"] == ("AC123", "token")
    assert call.kwargs["data"] == {
        "From": "whatsapp:+14155238886",
        "To": "whatsapp:+393331234567",
        "Body": "ciao",
    }


def test_send_text_with_messaging_service(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    _client(from_number="", messaging_service_sid="MG999").send_text("+393331234567", "ciao")

    data = http.calls[0].kwargs["data"]
    assert data["MessagingServiceSid"] == "MG999"
    assert "From" not in data


def test_send_template_uses_content_sid(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    client = _client(content_sids={"reminder_visita": "HXreminder"})
    client.send_template("+393331234567", "reminder_visita", {"2": "18:30", "1": "domani"})

    data = http.calls[0].kwargs["data"]
    assert data["ContentSid"] == "HXreminder"
    assert json.loads(data["ContentVariables"]) == {"1": "domani", "2": "18:30"}


def test_send_template_without_variables(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    _client().send_template("+393331234567", "reopener")

    assert "ContentVariables" not in http.calls[0].kwargs["data"]


def test_send_template_unmapped_raises(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    with pytest.raises(TemplateNotConfigured):
        _client(content_sids={}).send_template("+393331234567", "reopener")
    assert not http.calls


def test_missing_credentials_raise(monkeypatch):
    http = FakeHTTP()
    monkeypatch.setattr(httpx, "post", http)

    with pytest.raises(WhatsAppNotConfigured):
        TwilioWhatsAppClient("AC123", "token").send_text("+393331234567", "ciao")
    assert not http.calls


def test_is_configured():
    assert _client().is_configured() is True
    assert TwilioWhatsAppClient("AC123", "token").is_configured() is False
    assert TwilioWhatsAppClient("", "", from_number="+1").is_configured() is False


def test_signature_matches_twilio_algorithm():
    # Esempio dalla documentazione Twilio sull'ordinamento alfabetico dei parametri.
    url = "https://example.com/webhook"
    params = {"Body": "ciao", "From": "whatsapp:+393331234567"}
    expected = compute_signature("token", url, params)

    assert verify_signature("token", url, params, expected) is True
    # I parametri concatenati contano: cambiarne uno invalida la firma.
    assert verify_signature("token", url, {**params, "Body": "altro"}, expected) is False
    # Anche l'URL fa parte del payload firmato.
    assert verify_signature("token", url + "/x", params, expected) is False


def test_signature_rejected_without_token_or_header():
    params = {"Body": "ciao"}
    assert verify_signature("", "https://e.com/webhook", params, "abc") is False
    assert verify_signature("token", "https://e.com/webhook", params, "") is False
