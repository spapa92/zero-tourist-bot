"""API dashboard lead: autenticazione Basic Auth, lista e dettaglio contatti."""

from __future__ import annotations

import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.container import Container
from app.dashboard.api import router as dashboard_router
from app.dashboard.auth import basic_auth_middleware
from app.db import repository
from app.domain.slots import Slots
from tests.helpers import make_session_factory

USERNAME = "agente"
PASSWORD = "segreto"


def _auth_header(username: str, password: str) -> dict:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _settings(**overrides) -> Settings:
    base = {"dashboard_username": USERNAME, "dashboard_password": PASSWORD}
    base.update(overrides)
    return Settings(**base)


def _client(settings: Settings) -> tuple[TestClient, object]:
    session_factory = make_session_factory()
    container = Container(
        agency_config=None,
        llm=None,
        graph=None,
        whatsapp=None,
        calendar=None,
        session_factory=session_factory,
    )
    app = FastAPI()
    app.state.settings = settings
    app.state.container = container
    app.include_router(dashboard_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.middleware("http")(basic_auth_middleware)
    return TestClient(app), session_factory


def _seed_lead(session_factory, phone: str) -> None:
    with session_factory() as session:
        lead = repository.get_or_create_lead(session, phone)
        repository.add_message(session, lead, "user", "ciao")
        repository.add_message(session, lead, "bot", "risposta")
        repository.save_outcome(
            session, lead, "in_target", Slots(intento="comprare", budget=200000)
        )
        session.commit()


def test_leads_endpoint_requires_auth():
    client, _ = _client(_settings())

    response = client.get("/api/leads")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"].startswith("Basic")


def test_leads_endpoint_rejects_wrong_credentials():
    client, _ = _client(_settings())

    response = client.get("/api/leads", headers=_auth_header(USERNAME, "sbagliata"))

    assert response.status_code == 401


def test_leads_endpoint_denied_when_credentials_unset():
    client, _ = _client(_settings(dashboard_username="", dashboard_password=""))

    response = client.get("/api/leads", headers=_auth_header("", ""))

    assert response.status_code == 401


def test_leads_endpoint_with_auth_returns_seeded_leads():
    client, session_factory = _client(_settings())
    _seed_lead(session_factory, "+391111111")

    response = client.get("/api/leads", headers=_auth_header(USERNAME, PASSWORD))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["phone"] == "+391111111"
    assert body["items"][0]["latest_decision"] == "in_target"


def test_leads_search_filters_by_phone():
    client, session_factory = _client(_settings())
    _seed_lead(session_factory, "+391111111")
    _seed_lead(session_factory, "+392222222")

    response = client.get(
        "/api/leads", params={"q": "222"}, headers=_auth_header(USERNAME, PASSWORD)
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["phone"] == "+392222222"


def test_leads_pagination():
    client, session_factory = _client(_settings())
    for i in range(3):
        _seed_lead(session_factory, f"+39100000{i}")

    response = client.get(
        "/api/leads", params={"limit": 2, "offset": 1}, headers=_auth_header(USERNAME, PASSWORD)
    )

    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2


def test_lead_detail_returns_transcript_and_outcomes():
    client, session_factory = _client(_settings())
    _seed_lead(session_factory, "+391111111")

    response = client.get("/api/leads/+391111111", headers=_auth_header(USERNAME, PASSWORD))

    assert response.status_code == 200
    body = response.json()
    assert [m["role"] for m in body["messages"]] == ["user", "bot"]
    assert body["outcomes"][0]["slots"]["budget"] == 200000


def test_lead_detail_unknown_phone_returns_404():
    client, _ = _client(_settings())

    response = client.get("/api/leads/+390000000", headers=_auth_header(USERNAME, PASSWORD))

    assert response.status_code == 404


def test_webhook_path_stays_public_without_auth():
    client, _ = _client(_settings())

    response = client.get("/health")

    assert response.status_code == 200
