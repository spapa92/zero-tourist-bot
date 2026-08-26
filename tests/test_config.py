import pytest

from app.config.agency_config import AgencyConfig, load_agency_config


def test_load_example_config():
    config = load_agency_config("config/agency.example.yaml")
    assert config.agency_name
    assert "Milano" in config.served_zones
    assert config.min_budget == 150000
    assert config.budget_by_zone["Milano"] == 200000


def test_missing_required_field_rejected():
    with pytest.raises(Exception):
        AgencyConfig(website_url="https://www.esempio.it")


def test_wrong_type_rejected():
    with pytest.raises(Exception):
        AgencyConfig(agency_name="X", website_url="https://x", min_budget="non-numero")
