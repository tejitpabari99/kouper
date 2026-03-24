from typing import Optional, Any
from ..data.providers import PROVIDERS
from ..data.insurance import ACCEPTED_INSURANCES, SELF_PAY_RATES

def build_provider_directory() -> str:
    lines = []
    for p in PROVIDERS:
        lines.append(f"- {p.last_name}, {p.first_name} {p.certification} | {p.specialty}")
        for dept in p.departments:
            lines.append(f"  • {dept.name} | {dept.address} | {dept.phone} | {dept.hours}")
    return "\n".join(lines)

def build_session_state_section(session: Any) -> str:
    """Build a ## Current Session State section from a BookingSession object or dict."""
    if session is None:
        return ""

    # Support both dict and object access
    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    step = _get(session, "step", "unknown")
    active_idx = _get(session, "active_referral_index", 0)
    bookings = _get(session, "bookings", [])
    patient = _get(session, "patient") or {}

    if isinstance(patient, dict):
        referred = patient.get("referred_providers", [])
    else:
        referred = getattr(patient, "referred_providers", [])

    total_referrals = len(referred)

    lines = [
        "## Current Session State",
        f"Step: {step}",
        f"Active Referral: {active_idx + 1} of {total_referrals}",
        "",
    ]

    if bookings:
        lines.append("### Completed Bookings")
        for b in bookings:
            def bg(key, default=None):
                if isinstance(b, dict):
                    return b.get(key, default)
                return getattr(b, key, default)
            ref_num = bg("referral_index", 0) + 1
            specialty = bg("specialty", "Unknown")
            appt_type = bg("appointment_type", "")
            provider_name = bg("provider_name", "")
            location = bg("location", "")
            lines.append(
                f"- Referral {ref_num} ({specialty}): {appt_type} with {provider_name} at {location}"
            )
        lines.append("")

    pending = []
    for i, ref in enumerate(referred):
        booked_indices = []
        for b in bookings:
            if isinstance(b, dict):
                booked_indices.append(b.get("referral_index"))
            else:
                booked_indices.append(getattr(b, "referral_index", None))
        if i not in booked_indices:
            if isinstance(ref, dict):
                spec = ref.get("specialty", "Unknown")
            else:
                spec = getattr(ref, "specialty", "Unknown")
            pending.append((i + 1, spec))

    if pending:
        lines.append("### Pending Referrals")
        for ref_num, spec in pending:
            lines.append(f"- Referral {ref_num} ({spec}): Not yet booked")

    return "\n".join(lines)


def build_system_prompt(patient_context: Optional[str] = None, session: Any = None) -> str:
    insurances = "\n".join(f"- {ins}" for ins in ACCEPTED_INSURANCES)
    rates = "\n".join(f"- {spec}: ${rate:.0f}" for spec, rate in SELF_PAY_RATES.items())
    context = patient_context or "No patient loaded yet."
    prompt = f"""You are a Care Coordinator Assistant helping nurses book appointments for patients following hospital discharge.

## Provider Directory
{build_provider_directory()}

## Appointment Rules
- NEW: 30 minutes, patient arrives 30 minutes early
- ESTABLISHED: 15 minutes, patient arrives 10 minutes early
- ESTABLISHED if patient had a COMPLETED visit in the same specialty within 5 years
- No-shows and cancellations do NOT count — only completed visits

## Accepted Insurances
{insurances}

## Self-Pay Rates (when insurance not accepted)
{rates}

## Your Role
Guide the nurse step by step. Use tools for accurate data — never guess. Proactively surface alternatives. Always include arrival time guidance. Flag any no-show history.

## Current Patient Context
{context}

## Tool Error Handling
When a tool returns a result containing "error": true, relay the user_message field to the nurse verbatim.
Do not expose error codes, stack traces, or technical details.
Offer the most helpful next step: suggest retrying, trying an alternative provider, or contacting the system administrator as appropriate."""
    if session is not None:
        session_section = build_session_state_section(session)
        if session_section:
            prompt += "\n\n" + session_section
    return prompt

def build_patient_context(patient: Optional[dict]) -> str:
    if not patient:
        return "No patient loaded."
    lines = [f"Patient: {patient.get('name')} | DOB: {patient.get('dob')} | PCP: {patient.get('pcp')}"]
    lines.append("Referred providers:")
    for r in patient.get("referred_providers", []):
        lines.append(f"  - {r.get('provider') or 'TBD'} ({r.get('specialty')})")
    lines.append("Appointment history:")
    for a in patient.get("appointments", []):
        lines.append(f"  - {a.get('date')} | {a.get('provider')} | {a.get('status')}")
    return "\n".join(lines)
