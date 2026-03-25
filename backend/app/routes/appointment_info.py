"""
Appointment info route — pre-fetches type and availability for the booking UI.

The frontend calls this endpoint when the nurse selects a provider and
specialty, combining appointment type determination and availability lookup
into a single response to reduce round trips.
"""
from fastapi import APIRouter, HTTPException, Query
from ..session_store import store
from ..logic.appointment_type import determine_appointment_type
from ..logic.availability import check_availability
from ..models.patient import PatientData

router = APIRouter(prefix="/session", tags=["appointment-info"])


@router.get("/{session_id}/appointment-info")
def get_appointment_info(
    session_id: str,
    provider: str = Query(..., description="Provider name, e.g. 'Dr. Gregory House'"),
    specialty: str = Query(..., description="Specialty, e.g. 'Orthopedics'"),
):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.patient:
        raise HTTPException(status_code=400, detail="No patient loaded in session")

    patient = PatientData(**session.patient)

    appt_result = determine_appointment_type(patient, specialty)

    try:
        availability = check_availability(provider)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    locations = [
        {
            "name": loc.department_name,
            "days": loc.days,
            "hours": loc.hours,
            "address": loc.address,
            "phone": loc.phone,
        }
        for loc in availability.locations
    ]

    return {
        "appointment_type": appt_result.type,
        "duration_minutes": appt_result.duration_minutes,
        "arrive_early_minutes": appt_result.arrival_minutes_early,
        "reason": appt_result.reason,
        "locations": locations,
    }
