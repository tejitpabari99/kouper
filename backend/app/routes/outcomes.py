from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

from ..session_store import store
from ..outcome_store import add_outcome, get_outcomes_for_patient
from ..models.appointment import AppointmentOutcome

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


class LogOutcomeRequest(BaseModel):
    patient_id: str
    session_id: str
    referral_index: int
    provider_name: str
    specialty: str
    location: str
    appointment_date: str
    status: Literal["completed", "no-show", "cancelled"]
    nurse_notes: str = ""


@router.post("")
def log_outcome(body: LogOutcomeRequest):
    outcome = AppointmentOutcome(**body.model_dump())
    add_outcome(outcome)
    return outcome


@router.get("/patient/{patient_id}")
def get_patient_outcomes(patient_id: str):
    outcomes = get_outcomes_for_patient(patient_id)
    return {"patient_id": patient_id, "outcomes": outcomes}
