from typing import Optional, List

from app.models.appointment import InsuranceResult
from app.data.insurance import ACCEPTED_INSURANCES, SELF_PAY_RATES, PRIOR_AUTH_REQUIRED
from app.data.providers import PROVIDERS


def _find_provider(provider_name: str):
    """Find a provider by partial name match (case-insensitive last name)."""
    name_lower = provider_name.lower()
    for p in PROVIDERS:
        if p.last_name.lower() in name_lower or name_lower in p.full_name.lower():
            return p
    return None


def check_insurance(
    insurance_name: str,
    specialty: str,
    provider_name: Optional[str] = None,
) -> InsuranceResult:
    """
    Check if insurance is accepted. If provider_name given, check against that
    provider's specific list. Falls back to global list if provider not found.
    """
    provider = _find_provider(provider_name) if provider_name else None

    if provider and provider.accepted_insurances:
        # Provider-specific check (case-insensitive partial match)
        accepted = any(
            ins.lower() in insurance_name.lower() or insurance_name.lower() in ins.lower()
            for ins in provider.accepted_insurances
        )
    else:
        # Global fallback
        accepted = any(
            ins.lower() in insurance_name.lower() or insurance_name.lower() in ins.lower()
            for ins in ACCEPTED_INSURANCES
        )

    self_pay_rate = None
    matched_specialty = None
    if not accepted:
        for spec_key, rate in SELF_PAY_RATES.items():
            if spec_key.lower() == specialty.strip().lower():
                self_pay_rate = rate
                matched_specialty = spec_key
                break

    return InsuranceResult(
        accepted=accepted,
        insurance_name=insurance_name,
        self_pay_rate=self_pay_rate,
        specialty=matched_specialty,
    )


def get_alternative_providers(insurance_name: str, specialty: str) -> List[dict]:
    """Find providers in the same specialty who accept the given insurance."""
    alternatives = []
    for p in PROVIDERS:
        if p.specialty.lower() != specialty.lower():
            continue
        accepts = any(
            ins.lower() in insurance_name.lower() or insurance_name.lower() in ins.lower()
            for ins in p.accepted_insurances
        )
        if accepts:
            alternatives.append({
                "name": p.full_name,
                "specialty": p.specialty,
                "location": p.departments[0].name if p.departments else "",
                "accepting_new_patients": p.accepting_new_patients,
            })
    return alternatives


def check_prior_auth(specialty: str, insurance_name: str) -> bool:
    """Check if prior authorization is required for this specialty/insurance combo."""
    for (spec, ins), required in PRIOR_AUTH_REQUIRED.items():
        if spec.lower() == specialty.lower():
            if ins.lower() in insurance_name.lower() or insurance_name.lower() in ins.lower():
                return required
    return False
