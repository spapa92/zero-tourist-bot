from langgraph.checkpoint.memory import MemorySaver

from app.domain.slots import Slots
from app.graph.builder import build_graph, detect_exit
from tests.helpers import FakeCalendar, FakeLLM


def _make_graph(agency_config, responses=None, calendar=None):
    return build_graph(
        FakeLLM(responses),
        agency_config,
        calendar or FakeCalendar(),
        checkpointer=MemorySaver(),
    )


def test_welcome_on_first_contact(agency_config):
    graph = _make_graph(agency_config, {"ciao": Slots()})
    result = graph.invoke(
        {"phone": "1", "user_message": "ciao"},
        config={"configurable": {"thread_id": "lead1"}},
    )
    assert "Benvenuto" in result["reply"]
    assert "comprare, vendere o affittare" in result["reply"]


def test_fallback_question_order(agency_config):
    graph = _make_graph(
        agency_config,
        {
            "ciao": Slots(),
            "cerco di comprare": Slots(intento="comprare"),
            "a Milano": Slots(zona="Milano"),
        },
    )
    cfg = {"configurable": {"thread_id": "lead1"}}
    r1 = graph.invoke({"phone": "1", "user_message": "ciao"}, config=cfg)
    assert "comprare, vendere o affittare" in r1["reply"]

    r2 = graph.invoke({"phone": "1", "user_message": "cerco di comprare"}, config=cfg)
    assert "zona" in r2["reply"].lower()

    r3 = graph.invoke({"phone": "1", "user_message": "a Milano"}, config=cfg)
    assert "tipologia" in r3["reply"].lower()


def test_route_in_target_books_slot(agency_config):
    calendar = FakeCalendar()
    graph = _make_graph(
        agency_config,
        {
            "cerco un appartamento a Milano con budget 250k e mutuo pre-approvato": Slots(
                intento="comprare",
                zona="Milano",
                tipologia="appartamento",
                budget=250000,
                mutuo="pre_approvato",
            )
        },
        calendar=calendar,
    )
    result = graph.invoke(
        {
            "phone": "1",
            "user_message": "cerco un appartamento a Milano con budget 250k e mutuo pre-approvato",
        },
        config={"configurable": {"thread_id": "lead1"}},
    )
    assert result["decision"] == "in_target"
    assert "prenotato" in result["reply"]
    assert len(calendar.events) == 1


def test_route_out_target_congedo(agency_config):
    graph = _make_graph(
        agency_config,
        {
            "cerco a Torino con budget 100k": Slots(
                intento="comprare",
                zona="Torino",
                tipologia="appartamento",
                budget=100000,
                mutuo="pre_approvato",
            )
        },
    )
    result = graph.invoke(
        {"phone": "1", "user_message": "cerco a Torino con budget 100k"},
        config={"configurable": {"thread_id": "lead1"}},
    )
    assert result["decision"] == "out_target"
    assert agency_config.website_url in result["reply"]


def test_booking_failure_reports_error(agency_config):
    calendar = FakeCalendar(fail=True)
    graph = _make_graph(
        agency_config,
        {
            "tutto in target": Slots(
                intento="comprare",
                zona="Milano",
                tipologia="appartamento",
                budget=250000,
                mutuo="pre_approvato",
            )
        },
        calendar=calendar,
    )
    result = graph.invoke(
        {"phone": "1", "user_message": "tutto in target"},
        config={"configurable": {"thread_id": "lead1"}},
    )
    assert result["decision"] == "in_target"
    assert "problema" in result["reply"].lower()


def test_global_exit_human(agency_config):
    graph = _make_graph(agency_config)
    result = graph.invoke(
        {"phone": "1", "user_message": "voglio parlare con un umano"},
        config={"configurable": {"thread_id": "lead1"}},
    )
    assert result["decision"] == "exit"
    assert "agente" in result["reply"]


def test_global_exit_stop(agency_config):
    graph = _make_graph(agency_config)
    result = graph.invoke(
        {"phone": "1", "user_message": "basta, non mi interessa"},
        config={"configurable": {"thread_id": "lead1"}},
    )
    assert result["decision"] == "exit"


def test_detect_exit():
    assert detect_exit("voglio parlare con un umano") == "human"
    assert detect_exit("basta") == "stop"
    assert detect_exit("aiuto, non capisco") == "help"
    assert detect_exit("cerco casa a Milano") is None
