"""Integrazione Google Calendar per la creazione degli slot di visita."""

from __future__ import annotations

import datetime as dt
from typing import Protocol, runtime_checkable


@runtime_checkable
class CalendarClient(Protocol):
    def create_event(
        self, calendar_id: str, summary: str, start: dt.datetime, end: dt.datetime
    ) -> str: ...


def next_business_day_slot(now: dt.datetime | None = None) -> tuple[dt.datetime, dt.datetime]:
    """Propone uno slot di default: prossimo giorno lavorativo alle 10:00 (30 min)."""
    now = now or dt.datetime.now()
    day = now + dt.timedelta(days=1)
    while day.weekday() >= 5:  # sabato, domenica
        day += dt.timedelta(days=1)
    start = day.replace(hour=10, minute=0, second=0, microsecond=0)
    return start, start + dt.timedelta(minutes=30)


class GoogleCalendarClient:
    def __init__(self, credentials_path: str) -> None:
        self.credentials_path = credentials_path

    def _build_service(self):
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/calendar.events"]
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=scopes
        )
        return build("calendar", "v3", credentials=credentials)

    def create_event(
        self, calendar_id: str, summary: str, start: dt.datetime, end: dt.datetime
    ) -> str:
        service = self._build_service()
        body = {
            "summary": summary,
            "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Rome"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Rome"},
        }
        event = service.events().insert(calendarId=calendar_id, body=body).execute()
        return event["id"]
