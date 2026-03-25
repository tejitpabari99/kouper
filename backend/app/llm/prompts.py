"""
System prompt construction for the Care Coordinator LLM.

The system prompt is rebuilt on every message to ensure the model always
has fresh patient context, up-to-date session state (pending vs. completed
referrals), and a complete provider + insurance reference it can reason over
without hallucinating.
"""
from typing import Optional, Any
from ..data.providers import PROVIDERS
from ..data.insurance import ACCEPTED_INSURANCES, SELF_PAY_RATES

def build_provider_directory() -> str:
    """
    Render the complete provider list as a formatted string for injection into
    the system prompt.  Including this statically saves a tool call per turn
    and lets the model reason about all providers simultaneously.
    """
    lines = []
    for p in PROVIDERS:
        lines.append(f"- {p.last_name}, {p.first_name} {p.certification} | {p.specialty}")
        for dept in p.departments:
            lines.append(f"  • {dept.name} | {dept.address} | {dept.phone} | {dept.hours}")
    return "\n".join(lines)

def build_session_state_section(session: Any) -> str:
    """
    Build a '## Current Session State' block that summarises booking progress.

    Injecting this into the system prompt lets the model know exactly which
    referrals are done vs. pending without needing a dedicated tool call.
    Handles both BookingSession objects and plain dicts (serialized sessions).
    """
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

    # Compute pending referrals by subtracting booked indices from the full list.
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
    """
    Assemble the full system prompt for a care coordinator conversation turn.

    The prompt is structured as a reference document the model can scan:
    - Provider directory: all specialists with locations and hours
    - Appointment rules: NEW vs. ESTABLISHED criteria
    - Insurance and self-pay data: accepted plans and fallback rates
    - Role instructions: keep the model focused on the nurse's workflow
    - Co-location tip: a hard-coded scheduling optimization for two providers
      who share a location (Jefferson Hospital) and can be double-booked on the
      same day to minimize patient trips
    - Current patient context: the active patient's demographics and history
    - Session state: which referrals are done and which are pending

    Args:
        patient_context: Pre-formatted patient summary string from build_patient_context().
        session: BookingSession (or dict equivalent) for the current session.

    Returns:
        Complete system prompt string to pass to the Anthropic API.
    """
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

## Co-location Scheduling Tip
Dr. Gregory House and Dr. Temperance Brennan both practice at Jefferson Hospital, Claremont, NC (202 Maple St).
House is available Thu-Fri; Brennan is available Tue-Thu. They overlap on Thursdays.
If this patient has referrals that could use either provider, proactively suggest booking both on the same day at Jefferson to minimize patient trips.

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
    """
    Format a patient dict into a compact summary string for the system prompt.

    Pulls name, DOB, PCP, referred providers (with specialty), and full
    appointment history including status — the model uses history to determine
    appointment type and to flag no-show patterns.
    """
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
