from app.llm.fallback import RegexFallbackClient


def test_extract_budget_k():
    client = RegexFallbackClient()
    slots = client.extract_slots("cerco un appartamento con budget 200k")
    assert slots.budget == 200000


def test_extract_budget_full_number():
    client = RegexFallbackClient()
    slots = client.extract_slots("budget 250.000 euro")
    assert slots.budget == 250000


def test_extract_intent_and_type():
    client = RegexFallbackClient()
    slots = client.extract_slots("cerco un trilocale")
    assert slots.intento == "comprare"
    assert slots.tipologia == "appartamento"


def test_extract_zone():
    client = RegexFallbackClient(zones=["milano", "roma"])
    slots = client.extract_slots("cerco casa a Milano")
    assert slots.zona == "milano"


def test_extract_mortgage():
    client = RegexFallbackClient()
    slots = client.extract_slots("ho il mutuo pre-approvato")
    assert slots.mutuo == "pre_approvato"


def test_no_extraction_returns_empty():
    client = RegexFallbackClient()
    slots = client.extract_slots("ciao")
    assert slots.model_dump() == {
        "intento": None,
        "zona": None,
        "tipologia": None,
        "budget": None,
        "mutuo": None,
    }
