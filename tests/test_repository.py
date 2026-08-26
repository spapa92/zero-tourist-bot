from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import repository
from app.db.models import Base, Lead
from app.domain.slots import Slots


def _make_session_factory():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_lead_log_roundtrip():
    session_factory = _make_session_factory()
    with session_factory() as session:
        lead = repository.get_or_create_lead(session, "+3912345678")
        repository.add_message(session, lead, "user", "ciao")
        repository.save_outcome(
            session,
            lead,
            "in_target",
            Slots(intento="comprare", budget=200000),
        )
        session.commit()

    with session_factory() as session:
        lead = session.query(Lead).filter(Lead.phone == "+3912345678").one()
        assert lead.id is not None


def test_get_or_create_is_idempotent():
    session_factory = _make_session_factory()
    with session_factory() as session:
        first = repository.get_or_create_lead(session, "+3999999999")
        session.commit()
        second = repository.get_or_create_lead(session, "+3999999999")
        assert first.id == second.id
