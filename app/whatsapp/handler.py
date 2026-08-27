"""Gestione di un messaggio in entrata, condivisa da tutti i provider.

I webhook si occupano solo di autenticare la richiesta e normalizzarne il payload:
da qui in poi il flusso (lead log → grafo → risposta → outcome) è identico
qualunque sia il canale attivo.
"""

from __future__ import annotations

import datetime as dt

from app.db import repository
from app.domain.slots import Slots


def handle_inbound_message(container, phone: str, text: str) -> None:
    with container.session_factory() as session:
        lead = repository.get_or_create_lead(session, phone)
        lead.last_inbound_at = dt.datetime.now(dt.timezone.utc)
        repository.add_message(session, lead, "user", text)

        result = container.graph.invoke(
            {"phone": phone, "user_message": text},
            config={"configurable": {"thread_id": phone}},
        )

        reply = result.get("reply", "")
        container.whatsapp.send_reply(phone, reply, lead.last_inbound_at)
        repository.add_message(session, lead, "bot", reply)

        decision = result.get("decision")
        if decision:
            repository.save_outcome(
                session, lead, decision, Slots.model_validate(result.get("slots", {}))
            )
        session.commit()
