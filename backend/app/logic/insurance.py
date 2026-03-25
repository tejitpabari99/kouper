"""
Insurance verification logic for care coordinator workflows.

Handles three distinct questions the system needs to answer:
  1. Is a patient's insurance accepted by a given provider (or globally)?
  2. If not, what is the self-pay rate for this specialty?
  3. Are there alternative in-network providers for this specialty?
  4. Does this insurance/specialty combination require prior authorization?
"""
from typing import Optional, List

from app.models.appointment import InsuranceResult
from app.data.insurance import ACCEPTED_INSURANCES, SELF_PAY_RATES, PRIOR_AUTH_REQUIRED
from app.data.providers import PROVIDERS


def _find_provider(provider_name: str):
    """Find a provider by partial name match (case-insensitive last name).

    Uses substring matching in both directions to handle "Dr. House",
    "House", and "Gregory House" all resolving to the same provider.
    """
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
    Determine whether a patient's insurance is accepted.

    When a specific provider is given, checks that provider's individual
    accepted_insurances list.  Falls back to the global ACCEPTED_INSURANCES
    list if no provider match is found — useful when the nurse hasn't
    selected a provider yet.

    Partial matching on insurance names handles common variations
    (e.g. "BlueCross" matching "BlueCross BlueShield of NC").

    If insurance is not accepted, looks up the self-pay rate for the
    specialty so the nurse can immediately quote an out-of-pocket cost.

    Returns an InsuranceResult with accepted status and optional self_pay_rate.
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
        # Look up the self-pay rate so the nurse can immediately quote a cost
        # rather than having to ask a follow-up question.
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
    """
    Find in-network alternative providers when the primary provider doesn't
    accept the patient's insurance.

    Returns a list of providers in the same specialty that do accept the
    insurance, allowing the nurse to offer alternatives without a separate
    search step.
    """
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
    """
    Check if prior authorization is required for this specialty/insurance combo.

    Prior auth requirements are stored as (specialty, insurance) pairs in
    PRIOR_AUTH_REQUIRED.  Returns False (no auth needed) when no matching rule
    is found, which is the safe default for unlisted combinations.
    """
    for (spec, ins), required in PRIOR_AUTH_REQUIRED.items():
        if spec.lower() == specialty.lower():
            if ins.lower() in insurance_name.lower() or insurance_name.lower() in ins.lower():
                return required
    return False
