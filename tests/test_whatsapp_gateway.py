"""Gateway WhatsApp: selezione del canale attivo e webhook end-to-end per provider."""

import hashlib
import hmac
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.container import Container
from app.db.models import Lead, Message
from app.whatsapp.client import WhatsAppClient
from app.whatsapp.factory import build_whatsapp_client
from app.whatsapp.providers.meta import MetaWhatsAppClient
from app.whatsapp.providers.twilio import TwilioWhatsAppClient
from app.whatsapp.webhooks import build_webhook_router
from app.whatsapp.webhooks.twilio import compute_signature
from tests.helpers import FakeGraph, make_session_factory

APP_SECRET = "app-secret"
AUTH_TOKEN = "auth-token"


class SpyClient(WhatsAppClient):
    provider = "spy"

    def __init__(self) -> None:
        self.sent: list[tuple] = []

    def send_text(self, to, text):
        self.sent.append((to, text))
        return {"ok": True}

    def send_template(self, to, template_name, variables=None):
        self.sent.append((to, template_name))
        return {"ok": True}


def _settings(**overrides) -> Settings:
    base = {
        "whatsapp_provider": "meta",
        "whatsapp_app_secret": APP_SECRET,
        "whatsapp_verify_token": "verify-me",
        "twilio_account_sid": "AC123",
        "twilio_auth_token": AUTH_TOKEN,
        "twilio_whatsapp_number": "+14155238886",
    }
    base.update(overrides)
    return Settings(**base)


def _client(settings: Settings, graph: FakeGraph, whatsapp: SpyClient) -> tuple:
    session_factory = make_session_factory()
    container = Container(
        agency_config=None,
        llm=None,
        graph=graph,
        whatsapp=whatsapp,
        calendar=None,
        session_factory=session_factory,
    )
    app = FastAPI()
    app.state.settings = settings
    app.state.container = container
    app.include_router(build_webhook_router(settings.whatsapp_provider))
    return TestClient(app), session_factory


# ── Selezione del provider ───────────────────────────────────────────────


def test_factory_builds_meta_by_default():
    client = build_whatsapp_client(_settings())
    assert isinstance(client, MetaWhatsAppClient)
    assert client.provider == "meta"


def test_factory_builds_twilio():
    settings = _settings(
        whatsapp_provider="twilio",
        twilio_content_sid_reopener="HXreopener",
        twilio_content_sid_reminder="HXreminder",
    )
    client = build_whatsapp_client(settings)
    assert isinstance(client, TwilioWhatsAppClient)
    assert client.content_sids == {"reopener": "HXreopener", "reminder_visita": "HXreminder"}


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError):
        _settings(whatsapp_provider="360dialog")


def test_provider_name_is_normalized():
    assert _settings(whatsapp_provider="  TWILIO ").whatsapp_provider == "twilio"


def test_only_the_active_provider_webhook_is_mounted():
    graph = FakeGraph()
    # Con Twilio attivo il challenge GET di Meta non esiste.
    client, _ = _client(_settings(whatsapp_provider="twilio"), graph, SpyClient())
    assert client.get("/webhook", params={"hub.mode": "subscribe"}).status_code == 405

    # Con Meta attivo il challenge GET risponde.
    client, _ = _client(_settings(), graph, SpyClient())
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"


# ── Webhook Meta ─────────────────────────────────────────────────────────


def _meta_payload(phone: str, text: str) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": phone,
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


def test_meta_webhook_processes_message():
    graph = FakeGraph({"reply": "Benvenuto!"})
    whatsapp = SpyClient()
    client, session_factory = _client(_settings(), graph, whatsapp)

    body = json.dumps(_meta_payload("393331234567", "ciao")).encode()
    signature = "sha256=" + hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert graph.calls == [{"phone": "393331234567", "user_message": "ciao"}]
    assert whatsapp.sent == [("393331234567", "Benvenuto!")]
    with session_factory() as session:
        assert session.query(Lead).filter(Lead.phone == "393331234567").one()
        assert session.query(Message).count() == 2


def test_meta_webhook_rejects_bad_signature():
    graph = FakeGraph()
    client, _ = _client(_settings(), graph, SpyClient())

    response = client.post(
        "/webhook",
        json=_meta_payload("393331234567", "ciao"),
        headers={"X-Hub-Signature-256": "sha256=bad"},
    )

    assert response.status_code == 403
    assert not graph.calls


# ── Webhook Twilio ───────────────────────────────────────────────────────


def _twilio_post(client: TestClient, params: dict, *, sign: bool = True) -> object:
    headers = {}
    if sign:
        url = "http://testserver/webhook"
        headers["X-Twilio-Signature"] = compute_signature(AUTH_TOKEN, url, params)
    return client.post("/webhook", data=params, headers=headers)


def test_twilio_webhook_processes_message():
    graph = FakeGraph({"reply": "Benvenuto!"})
    whatsapp = SpyClient()
    settings = _settings(whatsapp_provider="twilio")
    client, session_factory = _client(settings, graph, whatsapp)

    params = {
        "From": "whatsapp:+393331234567",
        "To": "whatsapp:+14155238886",
        "Body": "ciao",
        "MessageSid": "SM1",
    }
    response = _twilio_post(client, params)

    assert response.status_code == 200
    assert graph.calls == [{"phone": "+393331234567", "user_message": "ciao"}]
    assert whatsapp.sent == [("+393331234567", "Benvenuto!")]
    with session_factory() as session:
        assert session.query(Lead).filter(Lead.phone == "+393331234567").one()


def test_twilio_webhook_rejects_bad_signature():
    graph = FakeGraph()
    settings = _settings(whatsapp_provider="twilio")
    client, _ = _client(settings, graph, SpyClient())

    response = client.post(
        "/webhook",
        data={"From": "whatsapp:+393331234567", "Body": "ciao"},
        headers={"X-Twilio-Signature": "bad"},
    )

    assert response.status_code == 403
    assert not graph.calls


def test_twilio_webhook_rejects_missing_signature():
    graph = FakeGraph()
    settings = _settings(whatsapp_provider="twilio")
    client, _ = _client(settings, graph, SpyClient())

    response = _twilio_post(client, {"From": "whatsapp:+39333", "Body": "ciao"}, sign=False)

    assert response.status_code == 403
    assert not graph.calls


def test_twilio_webhook_can_skip_signature_validation():
    graph = FakeGraph({"reply": "ok"})
    settings = _settings(whatsapp_provider="twilio", twilio_validate_signature=False)
    client, _ = _client(settings, graph, SpyClient())

    response = _twilio_post(client, {"From": "whatsapp:+39333", "Body": "ciao"}, sign=False)

    assert response.status_code == 200
    assert graph.calls


def test_twilio_webhook_ignores_messages_without_text():
    graph = FakeGraph()
    settings = _settings(whatsapp_provider="twilio")
    client, _ = _client(settings, graph, SpyClient())

    params = {"From": "whatsapp:+393331234567", "Body": "", "NumMedia": "1"}
    response = _twilio_post(client, params)

    assert response.status_code == 200
    assert not graph.calls


def test_twilio_webhook_uses_configured_public_url():
    """Dietro proxy la firma è calcolata sull'URL pubblico, non su quello interno."""
    graph = FakeGraph({"reply": "ok"})
    settings = _settings(
        whatsapp_provider="twilio",
        twilio_webhook_url="https://bot.agenzia.it/webhook",
    )
    client, _ = _client(settings, graph, SpyClient())

    params = {"From": "whatsapp:+393331234567", "Body": "ciao"}
    signature = compute_signature(AUTH_TOKEN, "https://bot.agenzia.it/webhook", params)
    response = client.post("/webhook", data=params, headers={"X-Twilio-Signature": signature})

    assert response.status_code == 200
    assert graph.calls
