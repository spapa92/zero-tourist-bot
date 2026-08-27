"""API JSON della dashboard lead: lista contatti e dettaglio conversazione."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.dashboard.schemas import (
    LeadDetailResponse,
    LeadListItem,
    LeadListResponse,
    MessageOut,
    OutcomeOut,
)
from app.db import repository

router = APIRouter(prefix="/api")


@router.get("/leads", response_model=LeadListResponse)
def list_leads(
    request: Request,
    q: str | None = Query(default=None, description="Filtro parziale sul numero di telefono"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> LeadListResponse:
    with request.app.state.container.session_factory() as session:
        leads, total = repository.list_leads(session, q, limit, offset)
        outcomes_by_lead = repository.get_latest_outcomes(session, [lead.id for lead in leads])

        items = [
            LeadListItem(
                phone=lead.phone,
                created_at=lead.created_at,
                last_inbound_at=lead.last_inbound_at,
                latest_decision=(outcomes_by_lead[lead.id].decision if lead.id in outcomes_by_lead else None),
                latest_appointment_status=(
                    outcomes_by_lead[lead.id].appointment_status if lead.id in outcomes_by_lead else None
                ),
            )
            for lead in leads
        ]

    return LeadListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/leads/{phone}", response_model=LeadDetailResponse)
def get_lead_detail(request: Request, phone: str) -> LeadDetailResponse:
    with request.app.state.container.session_factory() as session:
        lead = repository.get_lead_by_phone(session, phone)
        if lead is None:
            raise HTTPException(status_code=404, detail="Lead non trovato")

        messages = repository.list_messages_for_lead(session, lead.id)
        outcomes = repository.list_outcomes_for_lead(session, lead.id)

        return LeadDetailResponse(
            phone=lead.phone,
            created_at=lead.created_at,
            last_inbound_at=lead.last_inbound_at,
            messages=[
                MessageOut(role=m.role, content=m.content, created_at=m.created_at) for m in messages
            ],
            outcomes=[
                OutcomeOut(
                    decision=o.decision,
                    slots=o.slots,
                    appointment_status=o.appointment_status,
                    created_at=o.created_at,
                )
                for o in outcomes
            ],
        )
