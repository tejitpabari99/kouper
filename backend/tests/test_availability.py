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


def test_brennan_available_tuesday():
    """Brennan (Orthopedics) is Tu-Th at Jefferson Hospital → Tuesday is included."""
    result = check_availability("Brennan, Temperance")
    assert len(result.locations) == 1
    assert "Tuesday" in result.locations[0].days


def test_brennan_unavailable_monday():
    """Brennan is Tu-Th, so Monday should NOT be in her available days."""
    result = check_availability("Brennan, Temperance")
    for loc in result.locations:
        assert "Monday" not in loc.days


def test_grey_available_friday():
    """Grey is M-F, so Friday should be in her available days."""
    result = check_availability("Grey, Meredith")
    assert len(result.locations) == 1
    assert "Friday" in result.locations[0].days


def test_perry_unavailable_thursday():
    """Perry is M-W only, so Thursday should NOT be in her available days."""
    result = check_availability("Perry, Chris")
    for loc in result.locations:
        assert "Thursday" not in loc.days


def test_house_and_brennan_share_jefferson():
    """Both House (Th-F) and Brennan (Tu-Th) are at Jefferson Hospital — verify same location name."""
    house_result = check_availability("House, Gregory")
    brennan_result = check_availability("Brennan, Temperance")

    house_jefferson = next(
        (loc for loc in house_result.locations if "Jefferson" in loc.department_name), None
    )
    brennan_jefferson = next(
        (loc for loc in brennan_result.locations if "Jefferson" in loc.department_name), None
    )

    assert house_jefferson is not None, "House should have a Jefferson Hospital location"
    assert brennan_jefferson is not None, "Brennan should have a Jefferson Hospital location"
    assert house_jefferson.department_name == brennan_jefferson.department_name == "Jefferson Hospital"
