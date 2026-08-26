"""Accesso dati: lead, messaggi e outcome (lead log)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Lead, Message, Outcome
from app.domain.slots import Slots


def get_or_create_lead(session: Session, phone: str) -> Lead:
    lead = session.query(Lead).filter(Lead.phone == phone).one_or_none()
    if lead is None:
        lead = Lead(phone=phone)
        session.add(lead)
        session.flush()
    return lead


def add_message(session: Session, lead: Lead, role: str, content: str) -> None:
    session.add(Message(lead_id=lead.id, role=role, content=content))


def save_outcome(
    session: Session,
    lead: Lead,
    decision: str,
    slots: Slots,
    appointment_status: str | None = None,
) -> None:
    session.add(
        Outcome(
            lead_id=lead.id,
            decision=decision,
            slots=slots.model_dump(),
            appointment_status=appointment_status,
        )
    )
