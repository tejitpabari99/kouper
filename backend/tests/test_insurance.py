import pytest
from app.logic.insurance import check_insurance


def test_aetna_accepted():
    result = check_insurance("Aetna", "Primary Care")
    assert result.accepted is True
    assert result.insurance_name == "Aetna"


def test_cigna_accepted():
    result = check_insurance("Cigna", "Surgery")
    assert result.accepted is True
    assert result.insurance_name == "Cigna"


def test_anthem_rejected():
    """Anthem is not in the accepted list."""
    result = check_insurance("Anthem", "Primary Care")
    assert result.accepted is False


def test_rejected_includes_self_pay_rate():
    """Anthem + Orthopedics → self-pay rate of $300."""
    result = check_insurance("Anthem", "Orthopedics")
    assert result.accepted is False
    assert result.self_pay_rate == 300.0


def test_all_accepted_insurances():
    """All 5 known accepted insurances should return accepted=True."""
    accepted_list = [
        "Medicaid",
        "United Health Care",
        "Blue Cross Blue Shield of North Carolina",
        "Aetna",
        "Cigna",
    ]
    for insurance in accepted_list:
        result = check_insurance(insurance, "Primary Care")
        assert result.accepted is True, f"Expected {insurance} to be accepted"


def test_case_insensitive_insurance_check():
    """'aetna' lowercase should match 'Aetna' and return accepted=True."""
    result = check_insurance("aetna", "Primary Care")
    assert result.accepted is True


def test_self_pay_rates_by_specialty():
    """Self-pay rates: Primary Care=$150, Orthopedics=$300, Surgery=$1000."""
    rates = {
        "Primary Care": 150.0,
        "Orthopedics": 300.0,
        "Surgery": 1000.0,
    }
    for specialty, expected_rate in rates.items():
        result = check_insurance("Anthem", specialty)
        assert result.accepted is False
        assert result.self_pay_rate == expected_rate, (
            f"Expected self-pay rate for {specialty} to be {expected_rate}, got {result.self_pay_rate}"
        )
