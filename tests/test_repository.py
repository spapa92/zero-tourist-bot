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


def test_get_lead_by_phone():
    session_factory = _make_session_factory()
    with session_factory() as session:
        repository.get_or_create_lead(session, "+391111111")
        session.commit()

    with session_factory() as session:
        assert repository.get_lead_by_phone(session, "+391111111") is not None
        assert repository.get_lead_by_phone(session, "+390000000") is None


def test_list_leads_filters_by_phone_and_paginates():
    session_factory = _make_session_factory()
    phones = ["+391000001", "+392000002", "+393000003"]
    with session_factory() as session:
        for phone in phones:
            repository.get_or_create_lead(session, phone)
        session.commit()

    with session_factory() as session:
        leads, total = repository.list_leads(session, None, limit=10, offset=0)
        assert total == 3
        assert len(leads) == 3

        leads, total = repository.list_leads(session, "300000", limit=10, offset=0)
        assert total == 1
        assert leads[0].phone == "+393000003"

        leads, total = repository.list_leads(session, None, limit=1, offset=1)
        assert total == 3
        assert len(leads) == 1


def test_get_latest_outcomes_returns_most_recent_per_lead():
    session_factory = _make_session_factory()
    with session_factory() as session:
        lead = repository.get_or_create_lead(session, "+391111111")
        repository.save_outcome(session, lead, "fuori_target", Slots())
        repository.save_outcome(session, lead, "in_target", Slots(budget=200000))
        session.commit()
        lead_id = lead.id

    with session_factory() as session:
        outcomes_by_lead = repository.get_latest_outcomes(session, [lead_id])
        assert outcomes_by_lead[lead_id].decision == "in_target"


def test_list_messages_and_outcomes_for_lead_ordered_by_date():
    session_factory = _make_session_factory()
    with session_factory() as session:
        lead = repository.get_or_create_lead(session, "+391111111")
        repository.add_message(session, lead, "user", "primo")
        repository.add_message(session, lead, "bot", "secondo")
        repository.save_outcome(session, lead, "in_target", Slots())
        session.commit()
        lead_id = lead.id

    with session_factory() as session:
        messages = repository.list_messages_for_lead(session, lead_id)
        assert [m.content for m in messages] == ["primo", "secondo"]

        outcomes = repository.list_outcomes_for_lead(session, lead_id)
        assert len(outcomes) == 1
        assert outcomes[0].decision == "in_target"
