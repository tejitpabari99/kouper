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
