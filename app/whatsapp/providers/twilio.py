"""Provider WhatsApp basato su Twilio (Programmable Messaging + Content API).

Twilio non usa i nomi dei template come Meta: ogni template approvato è un *Content*
identificato da un `ContentSid` (HX...). La mappa `content_sids` traduce i nomi
logici dell'applicazione ("reopener", "reminder_visita") nei SID di Twilio.
"""

from __future__ import annotations

import json

import httpx

from app.whatsapp.client import (
    TemplateNotConfigured,
    WhatsAppClient,
    WhatsAppNotConfigured,
    sorted_variables,
)

API_ROOT = "https://api.twilio.com/2010-04-01"
ADDRESS_PREFIX = "whatsapp:"


def to_whatsapp_address(value: str) -> str:
    """Normalizza un numero nel formato indirizzo Twilio (`whatsapp:+39...`)."""
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith(ADDRESS_PREFIX):
        value = value[len(ADDRESS_PREFIX) :].strip()
    if not value.startswith("+"):
        value = "+" + value.lstrip("+")
    return f"{ADDRESS_PREFIX}{value}"


def from_whatsapp_address(value: str) -> str:
    """Estrae il numero in formato E.164 da un indirizzo Twilio (`whatsapp:+39...`)."""
    value = (value or "").strip()
    if value.startswith(ADDRESS_PREFIX):
        value = value[len(ADDRESS_PREFIX) :].strip()
    return value


class TwilioWhatsAppClient(WhatsAppClient):
    provider = "twilio"

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str = "",
        messaging_service_sid: str = "",
        content_sids: dict[str, str] | None = None,
    ) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.messaging_service_sid = messaging_service_sid
        self.content_sids = {k: v for k, v in (content_sids or {}).items() if v}
        self.base_url = f"{API_ROOT}/Accounts/{account_sid}/Messages.json"

    def is_configured(self) -> bool:
        has_sender = bool(self.from_number or self.messaging_service_sid)
        return bool(self.account_sid and self.auth_token and has_sender)

    def _sender(self) -> dict[str, str]:
        if self.messaging_service_sid:
            return {"MessagingServiceSid": self.messaging_service_sid}
        return {"From": to_whatsapp_address(self.from_number)}

    def send_text(self, to: str, text: str) -> dict:
        data = {**self._sender(), "To": to_whatsapp_address(to), "Body": text}
        return self._post(data)

    def send_template(
        self, to: str, template_name: str, variables: dict[str, str] | None = None
    ) -> dict:
        content_sid = self.content_sids.get(template_name)
        if not content_sid:
            raise TemplateNotConfigured(
                f"Nessun ContentSid Twilio configurato per il template '{template_name}': "
                "imposta la variabile TWILIO_CONTENT_SID_* corrispondente."
            )
        data = {**self._sender(), "To": to_whatsapp_address(to), "ContentSid": content_sid}
        params = sorted_variables(variables)
        if params:
            data["ContentVariables"] = json.dumps(dict(params))
        return self._post(data)

    def _post(self, data: dict[str, str]) -> dict:
        if not self.is_configured():
            raise WhatsAppNotConfigured(
                "Provider Twilio non configurato: imposta TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN "
                "e TWILIO_WHATSAPP_NUMBER (oppure TWILIO_MESSAGING_SERVICE_SID)."
            )
        response = httpx.post(
            self.base_url,
            data=data,
            auth=(self.account_sid, self.auth_token),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
