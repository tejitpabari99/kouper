import pytest
from app.logic.availability import check_availability


def test_availability_house_returns_two_locations():
    """House is registered at two departments."""
    result = check_availability("House, Gregory")
    assert len(result.locations) == 2


def test_availability_house_ppth_days():
    """PPTH Orthopedics is M-W → Monday, Tuesday, Wednesday."""
    result = check_availability("House, Gregory")
    ppth = next(loc for loc in result.locations if "PPTH" in loc.department_name)
    assert ppth.days == ["Monday", "Tuesday", "Wednesday"]


def test_availability_house_jefferson_days():
    """Jefferson Hospital for House is Th-F → Thursday, Friday."""
    result = check_availability("House, Gregory")
    jefferson = next(loc for loc in result.locations if "Jefferson" in loc.department_name)
    assert jefferson.days == ["Thursday", "Friday"]


def test_availability_grey():
    """Grey is M-F → all 5 weekdays."""
    result = check_availability("Grey, Meredith")
    assert len(result.locations) == 1
    assert result.locations[0].days == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def test_availability_brennan_days():
    """Brennan is Tu-Th → Tuesday, Wednesday, Thursday."""
    result = check_availability("Brennan, Temperance")
    assert len(result.locations) == 1
    assert result.locations[0].days == ["Tuesday", "Wednesday", "Thursday"]


def test_name_normalization():
    """'Dr. Gregory House' should resolve the same as 'House, Gregory'."""
    result_full = check_availability("Dr. Gregory House")
    result_last_first = check_availability("House, Gregory")
    assert result_full.provider_name == result_last_first.provider_name
    assert len(result_full.locations) == len(result_last_first.locations)
