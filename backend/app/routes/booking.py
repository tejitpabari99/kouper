"""
Booking confirmation route — the core write operation of the care coordinator workflow.

When the nurse confirms a booking, this route:
  1. Looks up provider availability to attach location details (phone, address, hours)
  2. Runs appointment type determination (NEW vs. ESTABLISHED) based on patient history
  3. Creates a CompletedBooking record and adds it to the session
  4. Generates three reminder records if patient preferences are on file
  5. Advances the session step (to 'complete' if all referrals are booked, else back
     to 'referrals_overview' for the next pending referral)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..session_store import store
from ..models.session import CompletedBooking
from ..logic.availability import check_availability
from ..logic.appointment_type import determine_appointment_type
from ..logic.reminders import schedule_reminders
from ..models.patient import PatientData
from ..audit_log import append_audit_entry, AuditLogEntry

router = APIRouter(prefix="/session", tags=["booking"])

class ConfirmBookingRequest(BaseModel):
    referral_index: int      # Which referral in the patient's referred_providers list
    provider_name: str
    specialty: str
    location_name: str
    nurse_notes: str = ""
    scheduled_datetime: Optional[str] = None  # ISO datetime if a specific slot was selected

@router.post("/{session_id}/confirm-booking")
def confirm_booking(session_id: str, body: ConfirmBookingRequest):
    """
    Confirm a booking for one referral and persist it to the session.

    Idempotent for the same referral_index — an existing booking for that
    index is replaced, so re-submitting after a correction works correctly.
    """
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.patient:
        raise HTTPException(status_code=400, detail="No patient loaded")

    # Get availability for this provider to find location details (phone, address)
    try:
        avail = check_availability(body.provider_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    location = next((loc for loc in avail.locations if loc.department_name == body.location_name), None)

    # Determine appointment type from patient's appointment history
    patient = PatientData(**session.patient)
    appt_type = determine_appointment_type(patient, body.specialty)

    booking = CompletedBooking(
        referral_index=body.referral_index,
        provider_name=body.provider_name,
        specialty=body.specialty,
        location=body.location_name,
        appointment_type=appt_type.type,
        duration_minutes=appt_type.duration_minutes,
        arrival_minutes_early=appt_type.arrival_minutes_early,
        provider_phone=location.phone if location else None,
        provider_address=location.address if location else None,
        provider_hours=location.hours if location else None,
        nurse_notes=body.nurse_notes,
    )
    if body.scheduled_datetime:
        booking.scheduled_date = body.scheduled_datetime

    # Replace any existing booking for this referral index (allow re-booking)
    session.bookings = [b for b in session.bookings if b.referral_index != body.referral_index]
    session.bookings.append(booking)

    # Generate queued reminder records if preferences are available
    if session.patient_preferences:
        patient_name = session.patient.get("name", "Patient") if session.patient else "Patient"
        new_reminders = schedule_reminders(booking, session.patient_preferences, patient_name)
        session.reminders.extend(new_reminders)

    # Advance session step: complete if all referrals are booked
    total_referrals = len(session.patient.get("referred_providers", []))
    if len(session.bookings) >= total_referrals:
        session.step = "complete"
    else:
        session.step = "referrals_overview"
        session.active_referral_index = body.referral_index + 1

    store.update(session)
    append_audit_entry(AuditLogEntry(
        timestamp=datetime.utcnow().isoformat() + "Z",
        type="system", actor="system",
        action="booking_confirmed",
        session_id=session_id,
        detail={
            "provider": body.provider_name,
            "specialty": body.specialty,
            "location": body.location_name,
            "referral_index": body.referral_index,
            "appointment_type": appt_type.type,
        },
    ))
    return booking

@router.get("/{session_id}/summary")
def get_summary(session_id: str):
    """Return a summary of the session suitable for the confirmation/handoff screen."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "patient": session.patient,
        "bookings": session.bookings,
        "preferences": session.patient_preferences,
        "step": session.step,
    }
