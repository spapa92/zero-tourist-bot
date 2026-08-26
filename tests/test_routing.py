from app.domain.slots import Slots
from app.routing.engine import route


def _slots(**overrides) -> Slots:
    base = dict(
        intento="comprare",
        zona="Milano",
        tipologia="appartamento",
        budget=250000,
        mutuo="pre_approvato",
    )
    base.update(overrides)
    return Slots(**base)


def test_in_target(agency_config):
    result = route(_slots(), agency_config)
    assert result.in_target is True
    assert result.reasons == []


def test_out_of_zone(agency_config):
    result = route(_slots(zona="Torino"), agency_config)
    assert result.in_target is False
    assert any("zona" in r for r in result.reasons)


def test_budget_below_threshold(agency_config):
    result = route(_slots(zona="Milano", budget=100000), agency_config)
    assert result.in_target is False
    assert any("budget" in r for r in result.reasons)


def test_mortgage_not_allowed(agency_config):
    result = route(_slots(mutuo="non_avviato"), agency_config)
    assert result.in_target is False
    assert any("mutuo" in r for r in result.reasons)


def test_intent_not_allowed(agency_config):
    result = route(_slots(intento="vendere"), agency_config)
    assert result.in_target is False
    assert any("intento" in r for r in result.reasons)
