import pytest

from app.domain.slots import Slots


def test_missing_fields_order():
    slots = Slots()
    assert slots.missing_fields() == ["intento", "zona", "tipologia", "budget", "mutuo"]


def test_partial_missing_fields():
    slots = Slots(intento="comprare", zona="Milano")
    assert slots.missing_fields() == ["tipologia", "budget", "mutuo"]


def test_is_complete():
    assert Slots().is_complete() is False
    complete = Slots(
        intento="comprare",
        zona="Milano",
        tipologia="appartamento",
        budget=200000,
        mutuo="pre_approvato",
    )
    assert complete.is_complete() is True


def test_budget_wrong_type_rejected():
    with pytest.raises(Exception):
        Slots(budget="abc")


def test_merge_does_not_overwrite_existing():
    current = Slots(intento="comprare")
    incoming = Slots(intento="vendere", zona="Milano")
    merged = current.merge(incoming)
    assert merged.intento == "comprare"
    assert merged.zona == "Milano"
