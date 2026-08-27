"""Accesso dati: lead, messaggi e outcome (lead log)."""

from __future__ import annotations

from sqlalchemy import func, select
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


def get_lead_by_phone(session: Session, phone: str) -> Lead | None:
    return session.query(Lead).filter(Lead.phone == phone).one_or_none()


def list_leads(
    session: Session, phone_query: str | None, limit: int, offset: int
) -> tuple[list[Lead], int]:
    query = session.query(Lead)
    if phone_query:
        query = query.filter(Lead.phone.contains(phone_query))

    total = query.count()
    leads = (
        query.order_by(Lead.last_inbound_at.desc().nullslast(), Lead.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return leads, total


def get_latest_outcomes(session: Session, lead_ids: list[int]) -> dict[int, Outcome]:
    if not lead_ids:
        return {}

    latest_ids_subquery = (
        select(Outcome.lead_id, func.max(Outcome.id).label("max_id"))
        .where(Outcome.lead_id.in_(lead_ids))
        .group_by(Outcome.lead_id)
        .subquery()
    )
    outcomes = (
        session.query(Outcome)
        .join(latest_ids_subquery, Outcome.id == latest_ids_subquery.c.max_id)
        .all()
    )
    return {outcome.lead_id: outcome for outcome in outcomes}


def list_messages_for_lead(session: Session, lead_id: int) -> list[Message]:
    return (
        session.query(Message)
        .filter(Message.lead_id == lead_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def list_outcomes_for_lead(session: Session, lead_id: int) -> list[Outcome]:
    return (
        session.query(Outcome)
        .filter(Outcome.lead_id == lead_id)
        .order_by(Outcome.created_at.asc())
        .all()
    )
