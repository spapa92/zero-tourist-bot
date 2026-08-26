"""Webhook Meta WhatsApp: verifica firma, challenge e gestione messaggi."""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.db import repository
from app.domain.slots import Slots

router = APIRouter()


def verify_signature(body: bytes, secret: str, signature: str) -> bool:
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.get("/webhook")
async def webhook_verify(request: Request) -> PlainTextResponse:
    settings = request.app.state.settings
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == (
        settings.whatsapp_verify_token or ""
    ):
        return PlainTextResponse(params.get("hub.challenge", ""), status_code=200)
    return PlainTextResponse("", status_code=403)


@router.post("/webhook")
async def webhook_receive(request: Request) -> JSONResponse:
    settings = request.app.state.settings

    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(body, settings.whatsapp_app_secret, signature):
        return JSONResponse({"status": "invalid signature"}, status_code=403)

    payload = await request.json()
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                _handle_message(
                    request,
                    message.get("from", ""),
                    message.get("text", {}).get("body", ""),
                )
    return JSONResponse({"status": "ok"})


def _handle_message(request: Request, phone: str, text: str) -> None:
    container = request.app.state.container
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
