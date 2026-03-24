from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..session_store import store
from ..models.session import CompletedBooking
from ..logic.availability import check_availability
from ..logic.appointment_type import determine_appointment_type
from ..models.patient import PatientData

router = APIRouter(prefix="/session", tags=["booking"])

class ConfirmBookingRequest(BaseModel):
    referral_index: int
    provider_name: str
    specialty: str
    location_name: str
    nurse_notes: str = ""

@router.post("/{session_id}/confirm-booking")
def confirm_booking(session_id: str, body: ConfirmBookingRequest):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.patient:
        raise HTTPException(status_code=400, detail="No patient loaded")

    # Get availability for this provider to find location details
    try:
        avail = check_availability(body.provider_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    location = next((loc for loc in avail.locations if loc.department_name == body.location_name), None)

    # Determine appointment type
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
    # Remove existing booking for this referral index if present
    session.bookings = [b for b in session.bookings if b.referral_index != body.referral_index]
    # Then append the new booking
    session.bookings.append(booking)

    # Check if all referrals are booked
    total_referrals = len(session.patient.get("referred_providers", []))
    if len(session.bookings) >= total_referrals:
        session.step = "complete"
    else:
        session.step = "referrals_overview"
        session.active_referral_index = body.referral_index + 1

    store.update(session)
    return booking

@router.get("/{session_id}/summary")
def get_summary(session_id: str):
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
