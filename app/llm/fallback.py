"""Fallback deterministico a regole/regex, usato quando l'LLM non è disponibile."""

from __future__ import annotations

import re

from app.domain.slots import Slots

_BUDGET_RE = re.compile(r"(\d[\d.]*)\s*(k|mila|milione|milioni|euro|€)?", re.IGNORECASE)

_INTENT_KEYWORDS = {
    "vendere": ["vendo", "vendere", "vendita"],
    "affittare": ["affitto", "affittare", "locazione", "in affitto"],
    "comprare": ["compro", "comprare", "cerco", "acquisto", "acquistare", "cercando"],
}

_MORTGAGE_KEYWORDS = {
    "non_avviato": ["non approvat", "non ancora", "nessun mutuo", "devo ancora", "non ho il mutuo"],
    "in_corso": ["mutuo in corso", "sto facendo il mutuo", "richiesto il mutuo"],
    "cash": ["cash", "contanti", "senza mutuo", "liquidita"],
    "pre_approvato": ["pre approvat", "preapprovat", "mutuo approvat"],
}

_TYPE_KEYWORDS = {
    "appartamento": ["appartamento", "bilocale", "trilocale", "quadrilocale", "attico"],
    "casa": ["casa", "villa", "villetta", "casale", "schiera"],
    "commerciale": ["commerciale", "ufficio", "negozio", "locale", "capannone"],
}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9àèéìòù ]", " ", text.lower())


def _extract_budget(text: str) -> int | None:
    match = _BUDGET_RE.search(text)
    if not match:
        return None
    raw = match.group(1).replace(".", "")
    try:
        value = int(raw)
    except ValueError:
        return None
    suffix = (match.group(2) or "").lower()
    if suffix == "k":
        value *= 1000
    elif suffix == "mila":
        value *= 1000
    elif suffix in ("milione", "milioni"):
        value *= 1_000_000
    return value


def _match(text: str, mapping: dict[str, list[str]]) -> str | None:
    normalized = _normalize(text)
    for key, keywords in mapping.items():
        if any(_normalize(kw) in normalized for kw in keywords):
            return key
    return None


class RegexFallbackClient:
    """Estrae slot con regex e dizionari di parole chiave (degradazione senza LLM)."""

    def __init__(self, zones: list[str] | None = None) -> None:
        self.zones = [_normalize(z) for z in (zones or [])]

    def extract_slots(self, text: str) -> Slots:
        normalized = _normalize(text)
        zona = next((z for z in self.zones if z in normalized), None)
        return Slots(
            intento=_match(text, _INTENT_KEYWORDS),
            zona=zona,
            tipologia=_match(text, _TYPE_KEYWORDS),
            budget=_extract_budget(text),
            mutuo=_match(text, _MORTGAGE_KEYWORDS),
        )
