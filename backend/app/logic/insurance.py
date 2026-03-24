from typing import Optional

from app.models.appointment import InsuranceResult
from app.data.insurance import ACCEPTED_INSURANCES, SELF_PAY_RATES


def check_insurance(insurance_name: str, specialty: str) -> InsuranceResult:
    """
    Check whether the given insurance is accepted.
    If not accepted, include the self-pay rate for the specialty (if available).
    Matching is case-insensitive.
    """
    # Case-insensitive match
    accepted = any(
        ins.lower() == insurance_name.strip().lower()
        for ins in ACCEPTED_INSURANCES
    )

    if accepted:
        return InsuranceResult(
            accepted=True,
            insurance_name=insurance_name,
        )

    # Not accepted — find self-pay rate
    self_pay_rate: Optional[float] = None
    matched_specialty: Optional[str] = None
    for spec_key, rate in SELF_PAY_RATES.items():
        if spec_key.lower() == specialty.strip().lower():
            self_pay_rate = rate
            matched_specialty = spec_key
            break

    return InsuranceResult(
        accepted=False,
        insurance_name=insurance_name,
        self_pay_rate=self_pay_rate,
        specialty=matched_specialty,
    )
