"""Adattatore Gemini Flash con output strutturato (JSON schema)."""

from __future__ import annotations

import json

import httpx

from app.domain.slots import Slots

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

_SLOTS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "intento": {"type": "STRING", "nullable": True},
        "zona": {"type": "STRING", "nullable": True},
        "tipologia": {"type": "STRING", "nullable": True},
        "budget": {"type": "INTEGER", "nullable": True},
        "mutuo": {"type": "STRING", "nullable": True},
    },
}

_SYSTEM_PROMPT = (
    "Sei un estrattore di informazioni per lead immobiliari. "
    "Dal messaggio dell'utente estrai i campi riconosciuti e lascia gli altri null. "
    "Normalizza i valori: intento in {comprare, vendere, affittare}; "
    "mutuo in {pre_approvato, cash, in_corso, non_avviato}; "
    "budget come intero in euro (es. '200k' diventa 200000)."
)


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.model = model

    def extract_slots(self, text: str) -> Slots:
        url = f"{GEMINI_BASE}/models/{self.model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _SLOTS_SCHEMA,
            },
        }
        response = httpx.post(
            url, json=payload, headers={"x-goog-api-key": self.api_key}, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        return Slots.model_validate(json.loads(raw))
