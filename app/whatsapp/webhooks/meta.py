"""Webhook Meta WhatsApp Cloud API: challenge di verifica, firma e messaggi in entrata."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.whatsapp.handler import handle_inbound_message

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
                phone = message.get("from", "")
                text = message.get("text", {}).get("body", "")
                if phone and text:
                    handle_inbound_message(request.app.state.container, phone, text)
    return JSONResponse({"status": "ok"})
