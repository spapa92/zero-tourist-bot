"""Slot di prequalifica del lead e ordine di fallback."""

from __future__ import annotations

from pydantic import BaseModel

# Ordine di priorità per la richiesta dei campi mancanti.
FIELD_ORDER = ["intento", "zona", "tipologia", "budget", "mutuo"]


class Slots(BaseModel):
    """Dati chiave raccolti durante la prequalifica."""

    intento: str | None = None
    zona: str | None = None
    tipologia: str | None = None
    budget: int | None = None
    mutuo: str | None = None

    def missing_fields(self) -> list[str]:
        """Campi ancora vuoti, nell'ordine di priorità di fallback."""
        return [f for f in FIELD_ORDER if getattr(self, f) is None]

    def is_complete(self) -> bool:
        return not self.missing_fields()

    def merge(self, other: "Slots") -> "Slots":
        """Fonde i campi non nulli di ``other`` nei propri, senza sovrascrivere i già presenti."""
        data = self.model_dump()
        for field, value in other.model_dump().items():
            if value is not None and data.get(field) is None:
                data[field] = value
        return Slots(**data)
