"""Costruzione del container a partire dalle impostazioni."""

from __future__ import annotations

from app.config.agency_config import load_agency_config
from app.config.settings import Settings
from app.container import Container
from app.db.session import make_engine, make_session_factory
from app.gcalendar.client import GoogleCalendarClient
from app.graph.builder import build_graph
from app.graph.checkpointer import build_checkpointer
from app.llm.fallback import RegexFallbackClient
from app.llm.gemini import GeminiClient
from app.whatsapp.factory import build_whatsapp_client


def build_container(settings: Settings) -> Container:
    agency_config = load_agency_config(settings.agency_config_path)

    if settings.llm_provider == "fallback" or not settings.gemini_api_key:
        llm = RegexFallbackClient(zones=agency_config.served_zones)
    else:
        llm = GeminiClient(settings.gemini_api_key, settings.gemini_model)

    calendar = (
        GoogleCalendarClient(settings.google_calendar_credentials)
        if settings.google_calendar_credentials
        else None
    )

    whatsapp = build_whatsapp_client(settings)

    checkpointer = build_checkpointer(
        settings.database_url if settings.database_url.startswith("postgres") else None
    )
    graph = build_graph(llm, agency_config, calendar, checkpointer=checkpointer)

    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    return Container(
        agency_config=agency_config,
        llm=llm,
        graph=graph,
        whatsapp=whatsapp,
        calendar=calendar,
        session_factory=session_factory,
    )
