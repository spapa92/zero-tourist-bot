"""Costruzione del grafo LangGraph di prequalifica (slot-filling flessibile)."""

from __future__ import annotations

import re

from langgraph.graph import END, START, StateGraph

from app.config.agency_config import AgencyConfig
from app.domain.slots import FIELD_ORDER, Slots
from app.gcalendar.client import CalendarClient, next_business_day_slot
from app.graph.state import ConversationState
from app.llm.client import LLMClient
from app.routing.engine import route

QUESTIONS = {
    "intento": "Stai cercando di comprare, vendere o affittare?",
    "zona": "In quale zona o città cerchi?",
    "tipologia": "Che tipologia di immobile ti interessa? (appartamento, casa, villa, commerciale)",
    "budget": "Qual è il tuo budget indicativo?",
    "mutuo": "Hai già una pre-approvazione del mutuo o paghi in contanti?",
}

_EXIT_HUMAN = re.compile(
    r"(umano|una persona|operatore|agente immobiliare|essere umano"
    r"|parlare con qualcuno|assistenza)"
)
_EXIT_STOP = re.compile(
    r"(^|\s)(stop|basta|annulla|lascia perdere|non mi interessa"
    r"|non sono interessat|no grazie)"
)
_EXIT_HELP = re.compile(r"(aiuto|help|come funziona|non capisco|non ho capito)")


def detect_exit(text: str) -> str | None:
    low = text.lower()
    if _EXIT_HUMAN.search(low):
        return "human"
    if _EXIT_STOP.search(low):
        return "stop"
    if _EXIT_HELP.search(low):
        return "help"
    return None


def build_graph(
    llm: LLMClient,
    config: AgencyConfig,
    calendar: CalendarClient | None = None,
    checkpointer=None,
):
    def classify(state: ConversationState) -> dict:
        text = state.get("user_message", "")
        exit_kind = detect_exit(text)
        if exit_kind:
            return {"action": "exit", "exit_kind": exit_kind}
        current = Slots.model_validate(state.get("slots", {}))
        extracted = llm.extract_slots(text)
        merged = current.merge(extracted)
        return {"slots": merged.model_dump(), "action": "route" if merged.is_complete() else "ask"}

    def ask(state: ConversationState) -> dict:
        slots = Slots.model_validate(state.get("slots", {}))
        field = slots.missing_fields()[0]
        question = QUESTIONS[field]
        if all(getattr(slots, f) is None for f in FIELD_ORDER):
            reply = f"Benvenuto su {config.agency_name}! Sono l'assistente virtuale. {question}"
        else:
            reply = question
        return {"reply": reply}

    def route_lead(state: ConversationState) -> dict:
        slots = Slots.model_validate(state.get("slots", {}))
        result = route(slots, config)
        if result.in_target:
            decision = "in_target"
            reply = _book_or_confirm(config, calendar, slots)
        else:
            decision = "out_target"
            reply = (
                f"Grazie per l'interesse! Al momento non riusciamo ad aiutarti con la tua"
                f" richiesta. Visita il nostro sito per maggiori informazioni: {config.website_url}"
            )
        return {"reply": reply, "decision": decision, "slots": slots.model_dump()}

    def finalize_exit(state: ConversationState) -> dict:
        kind = state.get("exit_kind")
        if kind == "human":
            reply = "Certo, ti metto in contatto con un nostro agente. Ti ricontatterà a breve."
        elif kind == "stop":
            reply = "Va bene, grazie e a presto!"
        else:
            reply = "Posso aiutarti! Dimmi pure: stai cercando di comprare, vendere o affittare?"
        return {"reply": reply, "decision": "exit"}

    graph = StateGraph(ConversationState)
    graph.add_node("classify", classify)
    graph.add_node("ask", ask)
    graph.add_node("route", route_lead)
    graph.add_node("exit", finalize_exit)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        lambda state: state.get("action", "ask"),
        {"ask": "ask", "route": "route", "exit": "exit"},
    )
    graph.add_edge("ask", END)
    graph.add_edge("route", END)
    graph.add_edge("exit", END)

    return graph.compile(checkpointer=checkpointer)


def _book_or_confirm(config: AgencyConfig, calendar: CalendarClient | None, slots: Slots) -> str:
    if calendar is None:
        return "Grazie! Ti ricontattiamo a breve per fissare la visita."
    try:
        start, end = next_business_day_slot()
        calendar.create_event(
            config.calendar_id or "primary",
            f"Visita {config.agency_name} - {slots.zona or ''}",
            start,
            end,
        )
        return (
            f"Perfetto! Ho prenotato la tua visita per {start:%d/%m/%Y alle %H:%M}. "
            "Ti aspettiamo!"
        )
    except Exception:
        return (
            "Abbiamo riscontrato un problema nel prenotare la tua visita. "
            "Un nostro agente ti ricontatterà a breve."
        )
