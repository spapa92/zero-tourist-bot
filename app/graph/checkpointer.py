"""Factory del checkpointer: Postgres in produzione, memoria in sviluppo/test."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver


def build_checkpointer(database_url: str | None = None):
    """Restituisce un checkpointer Postgres se disponibile, altrimenti in memoria."""
    if database_url and database_url.startswith("postgres"):
        try:
            import psycopg
            from langgraph.checkpoint.postgres import PostgresSaver

            conn = psycopg.connect(database_url, autocommit=True)
            saver = PostgresSaver(conn)
            saver.setup()
            return saver
        except Exception:
            # DB non raggiungibile o driver mancante: degrada a memoria.
            pass
    return MemorySaver()
