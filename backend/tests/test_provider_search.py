import pytest
from app.logic.provider_search import get_providers


def test_get_primary_care_providers():
    """Primary Care returns Grey and Perry."""
    providers = get_providers("Primary Care")
    last_names = {p.last_name for p in providers}
    assert "Grey" in last_names
    assert "Perry" in last_names
    assert len(providers) == 2


def test_get_orthopedics_providers():
    """Orthopedics returns House and Brennan."""
    providers = get_providers("Orthopedics")
    last_names = {p.last_name for p in providers}
    assert "House" in last_names
    assert "Brennan" in last_names
    assert len(providers) == 2


def test_get_surgery_providers():
    """Surgery returns only Yang."""
    providers = get_providers("Surgery")
    assert len(providers) == 1
    assert providers[0].last_name == "Yang"


def test_case_insensitive():
    """'primary care' (lowercase) should match 'Primary Care'."""
    providers = get_providers("primary care")
    assert len(providers) == 2


def test_search_orthopedics_returns_house_and_brennan():
    """Orthopedics search should return both House and Brennan."""
    providers = get_providers("Orthopedics")
    last_names = {p.last_name for p in providers}
    assert "House" in last_names
    assert "Brennan" in last_names


def test_search_surgery_returns_yang():
    """Surgery search should return Yang."""
    providers = get_providers("Surgery")
    last_names = {p.last_name for p in providers}
    assert "Yang" in last_names


def test_search_unknown_specialty_returns_empty():
    """'Dermatology' is not a known specialty — should return an empty list."""
    providers = get_providers("Dermatology")
    assert providers == []
