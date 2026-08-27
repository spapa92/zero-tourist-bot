"""Router webhook: viene montato solo quello del provider attivo."""

from __future__ import annotations

from fastapi import APIRouter

from app.whatsapp.factory import (
    PROVIDER_META,
    PROVIDER_TWILIO,
    SUPPORTED_PROVIDERS,
    normalize_provider,
)
from app.whatsapp.webhooks import meta as meta_webhook
from app.whatsapp.webhooks import twilio as twilio_webhook


def build_webhook_router(provider: str) -> APIRouter:
    """Restituisce il router `/webhook` del provider richiesto.

    Un solo canale è attivo alla volta: l'endpoint pubblico resta lo stesso
    (`POST /webhook`), cambia solo il formato accettato e la verifica di autenticità.
    """
    name = normalize_provider(provider)
    if name == PROVIDER_META:
        return meta_webhook.router
    if name == PROVIDER_TWILIO:
        return twilio_webhook.router
    raise ValueError(
        f"WHATSAPP_PROVIDER '{name}' non supportato: usa uno tra {', '.join(SUPPORTED_PROVIDERS)}."
    )
