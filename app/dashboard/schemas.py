"""Modelli di risposta JSON per la dashboard lead."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class LeadListItem(BaseModel):
    phone: str
    created_at: dt.datetime
    last_inbound_at: dt.datetime | None
    latest_decision: str | None
    latest_appointment_status: str | None


class LeadListResponse(BaseModel):
    items: list[LeadListItem]
    total: int
    limit: int
    offset: int


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: dt.datetime


class OutcomeOut(BaseModel):
    decision: str
    slots: dict
    appointment_status: str | None
    created_at: dt.datetime


class LeadDetailResponse(BaseModel):
    phone: str
    created_at: dt.datetime
    last_inbound_at: dt.datetime | None
    messages: list[MessageOut]
    outcomes: list[OutcomeOut]
