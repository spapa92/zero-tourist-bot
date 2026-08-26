"""Configurazione per agenzia: regole di routing come dati (non codice)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

# Radice del progetto (directory che contiene il pacchetto `app`).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class AgencyConfig(BaseModel):
    agency_name: str
    website_url: str
    served_zones: list[str] = Field(default_factory=list)
    min_budget: int = 0
    budget_by_zone: dict[str, int] = Field(default_factory=dict)
    allowed_intents: list[str] = Field(default_factory=lambda: ["comprare"])
    allowed_types: list[str] = Field(
        default_factory=lambda: ["appartamento", "casa", "villa", "commerciale"]
    )
    mortgage_allowed: list[str] = Field(default_factory=lambda: ["pre_approvato", "cash"])
    calendar_id: str | None = None


def load_agency_config(path: str | Path) -> AgencyConfig:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    return AgencyConfig.model_validate(raw)
