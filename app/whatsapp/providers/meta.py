"""Provider WhatsApp basato sulla Meta WhatsApp Business Cloud API."""

from __future__ import annotations

import httpx

from app.whatsapp.client import (
    WhatsAppClient,
    WhatsAppNotConfigured,
    sorted_variables,
)


class MetaWhatsAppClient(WhatsAppClient):
    provider = "meta"

    def __init__(
        self,
        token: str,
        phone_number_id: str,
        api_version: str = "v21.0",
        language_code: str = "it",
    ) -> None:
        self.token = token
        self.phone_number_id = phone_number_id
        self.language_code = language_code
        self.base_url = f"https://graph.facebook.com/{api_version}"

    def is_configured(self) -> bool:
        return bool(self.token and self.phone_number_id)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def send_text(self, to: str, text: str) -> dict:
        return self._post(
            {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text},
            }
        )

    def send_template(
        self, to: str, template_name: str, variables: dict[str, str] | None = None
    ) -> dict:
        payload: dict = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": self.language_code},
            },
        }
        params = sorted_variables(variables)
        if params:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": value} for _, value in params],
                }
            ]
        return self._post(payload)

    def _post(self, payload: dict) -> dict:
        if not self.is_configured():
            raise WhatsAppNotConfigured(
                "Provider Meta non configurato: imposta WHATSAPP_TOKEN e WHATSAPP_PHONE_NUMBER_ID."
            )
        response = httpx.post(
            f"{self.base_url}/{self.phone_number_id}/messages",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
