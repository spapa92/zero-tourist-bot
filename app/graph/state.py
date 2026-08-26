"""Stato della conversazione per il grafo LangGraph."""

from __future__ import annotations

from typing import TypedDict


class ConversationState(TypedDict, total=False):
    phone: str
    user_message: str
    slots: dict
    action: str
    exit_kind: str
    reply: str
    decision: str
