"""Client WhatsApp (Meta Cloud API) e gestione della finestra di servizio 24h."""

from __future__ import annotations

import datetime as dt

import httpx

TEMPLATE_REOPENER = "reopener"
TEMPLATE_REMINDER = "reminder_visita"


class WhatsAppClient:
    def __init__(self, token: str, phone_number_id: str, api_version: str = "v21.0") -> None:
        self.token = token
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.facebook.com/{api_version}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def send_text(self, to: str, text: str) -> dict:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        response = httpx.post(
            f"{self.base_url}/{self.phone_number_id}/messages",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def send_template(
        self, to: str, template_name: str, components: list[dict] | None = None
    ) -> dict:
        payload: dict = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {"name": template_name, "language": {"code": "it"}},
        }
        if components:
            payload["template"]["components"] = components
        response = httpx.post(
            f"{self.base_url}/{self.phone_number_id}/messages",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def send_reply(self, to: str, text: str, last_inbound_at: dt.datetime | None) -> dict:
        """Invia in formato libero se la finestra è aperta, altrimenti il template re-opener."""
        if is_window_open(last_inbound_at):
            return self.send_text(to, text)
        return self.send_template(to, TEMPLATE_REOPENER)


def is_window_open(
    last_inbound_at: dt.datetime | None, now: dt.datetime | None = None
) -> bool:
    if last_inbound_at is None:
        return False
    now = now or dt.datetime.now(dt.timezone.utc)
    last = last_inbound_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=dt.timezone.utc)
    return (now - last) < dt.timedelta(hours=24)
