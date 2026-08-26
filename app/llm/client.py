"""Interfaccia sottile verso il modello linguistico (swappabile)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.slots import Slots


@runtime_checkable
class LLMClient(Protocol):
    """Estrae gli slot di prequalifica da un messaggio utente."""

    def extract_slots(self, text: str) -> Slots: ...
