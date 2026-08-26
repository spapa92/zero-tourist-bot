"""Motore di routing config-driven: decide in/out target applicando la config."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.config.agency_config import AgencyConfig
from app.domain.slots import Slots


@dataclass
class RoutingResult:
    in_target: bool
    reasons: list[str] = field(default_factory=list)


def _matches(value: str | None, allowed: list[str]) -> bool:
    if value is None:
        return True
    if not allowed:
        return True
    normalized = value.lower()
    return any(a.lower() in normalized or normalized in a.lower() for a in allowed)


def route(slots: Slots, config: AgencyConfig) -> RoutingResult:
    reasons: list[str] = []

    if not _matches(slots.intento, config.allowed_intents):
        reasons.append("intento fuori target")
    if slots.zona is not None and not _matches(slots.zona, config.served_zones):
        reasons.append("zona fuori target")

    threshold = (
        config.budget_by_zone.get(slots.zona, config.min_budget)
        if slots.zona
        else config.min_budget
    )
    if slots.budget is not None and slots.budget < threshold:
        reasons.append("budget sotto soglia")

    if not _matches(slots.mutuo, config.mortgage_allowed):
        reasons.append("mutuo non adeguato")
    if slots.tipologia is not None and not _matches(slots.tipologia, config.allowed_types):
        reasons.append("tipologia fuori target")

    return RoutingResult(in_target=not reasons, reasons=reasons)
