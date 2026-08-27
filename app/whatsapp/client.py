"""Interfaccia comune dei provider WhatsApp e gestione della finestra di servizio 24h.

Il gateway supporta più canali (Meta Cloud API, Twilio), attivi **uno alla volta**:
il resto dell'applicazione dipende solo da questa interfaccia, mai dal provider concreto.
"""

from __future__ import annotations

import abc
import datetime as dt

TEMPLATE_REOPENER = "reopener"
TEMPLATE_REMINDER = "reminder_visita"


class WhatsAppNotConfigured(RuntimeError):
    """Il provider attivo non ha le credenziali necessarie per inviare messaggi."""


class TemplateNotConfigured(RuntimeError):
    """Il template richiesto non è mappato sul provider attivo."""


class WhatsAppClient(abc.ABC):
    """Contratto comune a tutti i provider di messaggistica WhatsApp.

    `variables` è la forma neutra dei parametri di un template: chiavi posizionali
    ("1", "2", ...) come le usa WhatsApp, tradotte da ogni provider nel proprio formato
    (componenti per Meta, `ContentVariables` per Twilio).
    """

    provider: str = ""

    def is_configured(self) -> bool:
        """True se il provider ha tutto il necessario per inviare messaggi."""
        return True

    @abc.abstractmethod
    def send_text(self, to: str, text: str) -> dict:
        """Invia un messaggio in formato libero (valido solo dentro la finestra 24h)."""

    @abc.abstractmethod
    def send_template(
        self, to: str, template_name: str, variables: dict[str, str] | None = None
    ) -> dict:
        """Invia un template approvato (unica opzione fuori dalla finestra 24h)."""

    def send_reply(self, to: str, text: str, last_inbound_at: dt.datetime | None) -> dict:
        """Invia in formato libero se la finestra è aperta, altrimenti il template re-opener."""
        if is_window_open(last_inbound_at):
            return self.send_text(to, text)
        return self.send_template(to, TEMPLATE_REOPENER)


def is_window_open(last_inbound_at: dt.datetime | None, now: dt.datetime | None = None) -> bool:
    if last_inbound_at is None:
        return False
    now = now or dt.datetime.now(dt.timezone.utc)
    last = last_inbound_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=dt.timezone.utc)
    return (now - last) < dt.timedelta(hours=24)


def sorted_variables(variables: dict[str, str] | None) -> list[tuple[str, str]]:
    """Ordina i parametri di un template per indice posizionale ("1", "2", ...)."""
    if not variables:
        return []

    def key(item: tuple[str, str]) -> tuple[int, str]:
        name = str(item[0])
        return (int(name), "") if name.isdigit() else (10**6, name)

    return [(str(k), str(v)) for k, v in sorted(variables.items(), key=key)]
