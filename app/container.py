"""Container di dependency injection dell'applicazione."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import sessionmaker

from app.config.agency_config import AgencyConfig
from app.gcalendar.client import CalendarClient
from app.llm.client import LLMClient
from app.whatsapp.client import WhatsAppClient


@dataclass
class Container:
    agency_config: AgencyConfig
    llm: LLMClient
    graph: object
    whatsapp: WhatsAppClient
    calendar: CalendarClient | None
    session_factory: sessionmaker
