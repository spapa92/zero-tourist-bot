import tempfile

from langgraph.checkpoint.sqlite import SqliteSaver

from app.domain.slots import Slots
from app.graph.builder import build_graph
from tests.helpers import FakeLLM


def test_state_persists_across_restart(agency_config):
    llm = FakeLLM(
        {
            "cerco di comprare": Slots(intento="comprare"),
            "a Milano": Slots(zona="Milano"),
        }
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/checkpoint.sqlite"

        # Prima "esecuzione" dell'app.
        with SqliteSaver.from_conn_string(path) as saver:
            graph = build_graph(llm, agency_config, None, checkpointer=saver)
            graph.invoke(
                {"phone": "1", "user_message": "cerco di comprare"},
                config={"configurable": {"thread_id": "lead1"}},
            )

        # "Riavvio": nuovo checkpointer sullo stesso file.
        with SqliteSaver.from_conn_string(path) as saver2:
            graph2 = build_graph(llm, agency_config, None, checkpointer=saver2)
            result = graph2.invoke(
                {"phone": "1", "user_message": "a Milano"},
                config={"configurable": {"thread_id": "lead1"}},
            )

        # Lo stato precedente (intento) è stato ripristinato:
        # il campo mancante successivo è "tipologia", non "intento".
        assert "tipologia" in result["reply"].lower()
