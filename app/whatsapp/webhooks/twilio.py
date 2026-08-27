"""Webhook Twilio WhatsApp: validazione firma `X-Twilio-Signature` e messaggi in entrata.

Twilio invia i messaggi come form `application/x-www-form-urlencoded` e firma la
richiesta con HMAC-SHA1 su `URL + parametri POST concatenati in ordine alfabetico`,
in base64 (https://www.twilio.com/docs/usage/security#validating-requests).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from collections.abc import Mapping
from urllib.parse import parse_qsl

from fastapi import APIRouter, Request, Response
from starlette.datastructures import URL

from app.whatsapp.handler import handle_inbound_message
from app.whatsapp.providers.twilio import from_whatsapp_address

router = APIRouter()

EMPTY_TWIML = "<?xml version='1.0' encoding='UTF-8'?><Response></Response>"


def compute_signature(auth_token: str, url: str, params: Mapping[str, str]) -> str:
    payload = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def verify_signature(auth_token: str, url: str, params: Mapping[str, str], signature: str) -> bool:
    if not auth_token or not signature:
        return False
    return hmac.compare_digest(compute_signature(auth_token, url, params), signature)


def public_url(request: Request, configured_url: str = "") -> str:
    """URL pubblico della richiesta, quello che Twilio ha effettivamente chiamato.

    Dietro un reverse proxy (Caddy) lo schema e l'host visti da FastAPI sono quelli
    interni: si usa `TWILIO_WEBHOOK_URL` se impostata, altrimenti gli header
    `X-Forwarded-*` propagati dal proxy.
    """
    if configured_url:
        return configured_url
    url: URL = request.url
    proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    host = request.headers.get("x-forwarded-host", "").split(",")[0].strip()
    if proto:
        url = url.replace(scheme=proto)
    if host:
        url = url.replace(netloc=host)
    return str(url)


async def form_params(request: Request) -> dict[str, str]:
    """Parametri POST di Twilio (`application/x-www-form-urlencoded`).

    Il body viene decodificato a mano invece di usare `request.form()` per non
    dipendere da `python-multipart`: Twilio non invia mai `multipart/form-data`.
    """
    body = await request.body()
    return dict(parse_qsl(body.decode("utf-8"), keep_blank_values=True))


@router.post("/webhook")
async def webhook_receive(request: Request) -> Response:
    settings = request.app.state.settings

    params = await form_params(request)

    if settings.twilio_validate_signature:
        signature = request.headers.get("X-Twilio-Signature", "")
        url = public_url(request, settings.twilio_webhook_url)
        if not verify_signature(settings.twilio_auth_token, url, params, signature):
            return Response(status_code=403)

    phone = from_whatsapp_address(params.get("From", ""))
    text = (params.get("Body") or "").strip()
    if phone and text:
        handle_inbound_message(request.app.state.container, phone, text)

    # Risposta vuota: il bot invia i messaggi via API, non via TwiML.
    return Response(content=EMPTY_TWIML, media_type="application/xml")
