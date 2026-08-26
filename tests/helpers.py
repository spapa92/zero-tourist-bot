"""Helper condivisi per i test."""

from __future__ import annotations

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
