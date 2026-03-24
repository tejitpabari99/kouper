from datetime import date, datetime
from typing import Optional, List

from app.models.patient import PatientData
from app.models.appointment import AppointmentTypeResult, AppointmentOutcome
from app.data.providers import PROVIDERS

# Cutoff: appointments within 1825 days (5 years) count as ESTABLISHED
ESTABLISHED_WINDOW_DAYS = 1825

TODAY = date(2026, 3, 24)


def _parse_date(date_str: str) -> date:
    """Parse dates like '3/05/18' or '8/12/24' (m/d/yy, 2000s assumed)."""
    parts = date_str.strip().split("/")
    month = int(parts[0])
    day = int(parts[1])
    year_short = int(parts[2])
    year = 2000 + year_short
    return date(year, month, day)


def _get_specialty_for_provider_name(provider_name: str) -> Optional[str]:
    """
    Match a provider display name like 'Dr. Gregory House' or 'Dr. Meredith Grey'
    against the PROVIDERS list and return their specialty.
    """
    # Normalize: strip "Dr." prefix and extra whitespace
    normalized = provider_name.strip()
    if normalized.startswith("Dr."):
        normalized = normalized[3:].strip()

    # normalized is now "Gregory House" or "Meredith Grey"
    for provider in PROVIDERS:
        if f"{provider.first_name} {provider.last_name}".lower() == normalized.lower():
            return provider.specialty
    return None


def determine_appointment_type(
    patient: PatientData,
    specialty: str,
    additional_outcomes: Optional[List[AppointmentOutcome]] = None,
) -> AppointmentTypeResult:
    """
    Determine whether a patient needs a NEW or ESTABLISHED appointment for a given specialty.

    Rules:
    1. Only completed appointments count (no-shows and cancellations excluded).
    2. Match the appointment's provider name to a specialty via the PROVIDERS list.
    3. If any completed appointment in the same specialty occurred within 5 years of today → ESTABLISHED.
    4. Otherwise → NEW.
    """
    most_recent_date: Optional[date] = None

    # Check local outcome records (completed only)
    if additional_outcomes:
        for outcome in additional_outcomes:
            if outcome.status != "completed":
                continue
            if outcome.specialty.lower() != specialty.lower():
                continue
            try:
                appt_date = date.fromisoformat(outcome.appointment_date)
            except ValueError:
                continue
            if most_recent_date is None or appt_date > most_recent_date:
                most_recent_date = appt_date

    for appt in patient.appointments:
        if appt.status != "completed":
            continue

        appt_specialty = _get_specialty_for_provider_name(appt.provider)
        if appt_specialty is None:
            continue

        if appt_specialty.lower() != specialty.lower():
            continue

        appt_date = _parse_date(appt.date)
        if most_recent_date is None or appt_date > most_recent_date:
            most_recent_date = appt_date

    if most_recent_date is not None:
        days_since = (TODAY - most_recent_date).days
        if days_since <= ESTABLISHED_WINDOW_DAYS:
            return AppointmentTypeResult(
                type="ESTABLISHED",
                duration_minutes=15,
                arrival_minutes_early=10,
                reason=(
                    f"Patient had a completed {specialty} appointment on "
                    f"{most_recent_date.strftime('%m/%d/%Y')} "
                    f"({days_since} days ago), which is within the 5-year window."
                ),
            )

    if most_recent_date is not None:
        days_since = (TODAY - most_recent_date).days
        reason = (
            f"Patient's most recent completed {specialty} appointment was on "
            f"{most_recent_date.strftime('%m/%d/%Y')} "
            f"({days_since} days ago), which is beyond the 5-year window. "
            f"No-shows and cancellations were excluded."
        )
    else:
        reason = (
            f"No completed {specialty} appointments found in patient history. "
            f"No-shows and cancellations were excluded."
        )

    return AppointmentTypeResult(
        type="NEW",
        duration_minutes=30,
        arrival_minutes_early=30,
        reason=reason,
    )
