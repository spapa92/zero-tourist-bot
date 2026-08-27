"""Selezione del provider WhatsApp attivo (uno alla volta) in base alle impostazioni."""

from __future__ import annotations

from app.config.settings import Settings
from app.whatsapp.client import (
    TEMPLATE_REMINDER,
    TEMPLATE_REOPENER,
    WhatsAppClient,
)
from app.whatsapp.providers.meta import MetaWhatsAppClient
from app.whatsapp.providers.twilio import TwilioWhatsAppClient

PROVIDER_META = "meta"
PROVIDER_TWILIO = "twilio"
SUPPORTED_PROVIDERS = (PROVIDER_META, PROVIDER_TWILIO)


def normalize_provider(provider: str | None) -> str:
    return (provider or PROVIDER_META).strip().lower()


def build_whatsapp_client(settings: Settings) -> WhatsAppClient:
    provider = normalize_provider(settings.whatsapp_provider)

    if provider == PROVIDER_META:
        return MetaWhatsAppClient(
            settings.whatsapp_token,
            settings.whatsapp_phone_number_id,
            settings.whatsapp_api_version,
        )

    if provider == PROVIDER_TWILIO:
        return TwilioWhatsAppClient(
            settings.twilio_account_sid,
            settings.twilio_auth_token,
            from_number=settings.twilio_whatsapp_number,
            messaging_service_sid=settings.twilio_messaging_service_sid,
            content_sids={
                TEMPLATE_REOPENER: settings.twilio_content_sid_reopener,
                TEMPLATE_REMINDER: settings.twilio_content_sid_reminder,
            },
        )

    raise ValueError(
        f"WHATSAPP_PROVIDER '{provider}' non supportato: "
        f"usa uno tra {', '.join(SUPPORTED_PROVIDERS)}."
    )
