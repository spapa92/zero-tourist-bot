"""Helper condivisi per i test."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.domain.slots import Slots


class FakeLLM:
    def __init__(self, responses: dict[str, Slots] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[str] = []

    def extract_slots(self, text: str) -> Slots:
        self.calls.append(text)
        return self.responses.get(text, Slots())


class FakeCalendar:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.events: list[tuple] = []

    def create_event(self, calendar_id, summary, start, end):
        if self.fail:
            raise RuntimeError("calendar down")
        self.events.append((calendar_id, summary, start, end))
        return "evt_123"


@dataclass
class HTTPCall:
    url: str
    kwargs: dict = field(default_factory=dict)


class FakeResponse:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload if payload is not None else {"ok": True}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeHTTP:
    """Sostituto di `httpx.post` che registra le chiamate senza uscire in rete."""

    def __init__(self, payload: dict | None = None) -> None:
        self.calls: list[HTTPCall] = []
        self.payload = payload

    def __call__(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append(HTTPCall(url=url, kwargs=kwargs))
        return FakeResponse(self.payload)


class FakeGraph:
    """Grafo LangGraph fittizio: restituisce sempre lo stesso risultato."""

    def __init__(self, result: dict | None = None) -> None:
        self.result = result if result is not None else {"reply": "risposta"}
        self.calls: list[dict] = []

    def invoke(self, state: dict, config: dict | None = None) -> dict:
        self.calls.append(state)
        return self.result


def make_session_factory() -> sessionmaker:
    """SQLite in memoria condiviso tra thread (TestClient gira su un thread separato)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
