from fastapi import APIRouter, HTTPException
from ..session_store import store
from ..logic.insurance import check_insurance, get_alternative_providers, check_prior_auth
from ..data.insurance import SELF_PAY_RATES

router = APIRouter(prefix="/session", tags=["insurance"])


@router.get("/{session_id}/insurance-check")
def insurance_check(session_id: str, provider: str, specialty: str):
    """
    Check if the current session's patient insurance is accepted by the given provider.
    Returns insurance status, self-pay rate, alternatives, prior auth flag, and patient script.
    """
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Nurse-entered insurance takes precedence over EHR data
    patient_insurance = session.insurance or (session.patient.get("insurance", "") if session.patient else "") or ""

    if not patient_insurance or patient_insurance.lower() == "self-pay":
        return {
            "patient_insurance": patient_insurance or "Unknown",
            "provider": provider,
            "accepted": None,  # unknown / self-pay
            "self_pay": True,
            "self_pay_rate": SELF_PAY_RATES.get(specialty, None),
            "specialty": specialty,
            "alternatives": [],
            "prior_auth_required": False,
            "patient_script": f"This patient is self-pay. The estimated rate for {specialty} is listed below.",
        }

    result = check_insurance(patient_insurance, specialty, provider_name=provider)
    alternatives = [] if result.accepted else get_alternative_providers(patient_insurance, specialty)
    prior_auth = check_prior_auth(specialty, patient_insurance)

    if result.accepted:
        script = f"{patient_insurance} is accepted at this provider."
        if prior_auth:
            script += f" Note: Prior authorization may be required for {specialty} with {patient_insurance}. Please contact the insurance before the appointment."
    else:
        rate_str = f"${result.self_pay_rate:.0f}" if result.self_pay_rate else "an estimated fee"
        alt_names = ", ".join(a["name"] for a in alternatives[:2]) if alternatives else None
        script = (
            f"I want to let you know that {patient_insurance} is not currently accepted at this provider. "
            f"The estimated out-of-pocket cost would be {rate_str} per visit. "
        )
        if alt_names:
            script += f"Alternatively, {alt_names} accepts your plan for {specialty}."
        else:
            script += "No covered in-network alternatives are currently available for this specialty."

    return {
        "patient_insurance": patient_insurance,
        "provider": provider,
        "accepted": result.accepted,
        "self_pay": False,
        "self_pay_rate": result.self_pay_rate,
        "specialty": specialty,
        "alternatives": alternatives,
        "prior_auth_required": prior_auth,
        "patient_script": script,
    }
