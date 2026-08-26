from langgraph.checkpoint.memory import MemorySaver

from app.domain.slots import Slots
from app.graph.builder import build_graph
from tests.helpers import FakeCalendar, FakeLLM


def test_full_conversation_in_target(agency_config):
    calendar = FakeCalendar()
    llm = FakeLLM(
        {
            "ciao": Slots(),
            "vorrei comprare": Slots(intento="comprare"),
            "in zona Milano": Slots(zona="Milano"),
            "un appartamento": Slots(tipologia="appartamento"),
            "budget 250k": Slots(budget=250000),
            "mutuo pre-approvato": Slots(mutuo="pre_approvato"),
        }
    )
    graph = build_graph(llm, agency_config, calendar, checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "lead1"}}

    replies = []
    for message in [
        "ciao",
        "vorrei comprare",
        "in zona Milano",
        "un appartamento",
        "budget 250k",
        "mutuo pre-approvato",
    ]:
        result = graph.invoke({"phone": "1", "user_message": message}, config=cfg)
        replies.append(result["reply"])

    assert "Benvenuto" in replies[0]
    assert "prenotato" in replies[-1]
    assert len(calendar.events) == 1
    # Decisione finale in target
    final = graph.invoke(
        {"phone": "1", "user_message": "mutuo pre-approvato"}, config=cfg
    )
    assert final["decision"] == "in_target"


def test_full_conversation_out_target(agency_config):
    llm = FakeLLM(
        {
            "ciao": Slots(),
            "vorrei comprare": Slots(intento="comprare"),
            "a Torino": Slots(zona="Torino"),
            "una casa": Slots(tipologia="casa"),
            "budget 100k": Slots(budget=100000),
            "mutuo non avviato": Slots(mutuo="non_avviato"),
        }
    )
    graph = build_graph(llm, agency_config, None, checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "lead2"}}

    replies = []
    for message in [
        "ciao",
        "vorrei comprare",
        "a Torino",
        "una casa",
        "budget 100k",
        "mutuo non avviato",
    ]:
        result = graph.invoke({"phone": "2", "user_message": message}, config=cfg)
        replies.append(result["reply"])

    assert agency_config.website_url in replies[-1]
