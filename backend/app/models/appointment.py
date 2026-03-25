"""
Result models for appointment-related logic operations.

These models are returned by the logic layer and serialized to JSON for both
LLM tool results and REST API responses.
"""
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
import uuid
from datetime import datetime


class AppointmentTypeResult(BaseModel):
    """Result of the NEW vs. ESTABLISHED determination for a patient/specialty pair."""
    type: Literal["NEW", "ESTABLISHED"]
    duration_minutes: int       # NEW=30, ESTABLISHED=15
    arrival_minutes_early: int  # NEW=30, ESTABLISHED=10
    reason: str                 # Human-readable explanation surfaced to the nurse


class DepartmentAvailability(BaseModel):
    """Availability and contact info for one provider location/department."""
    department_name: str
    days: List[str]     # e.g. ["Monday", "Tuesday", "Wednesday"]
    hours: str          # e.g. "9am-5pm"
    phone: str
    address: str


class AvailabilityResult(BaseModel):
    """All practice locations and their availability for a given provider."""
    provider_name: str
    specialty: str
    locations: List[DepartmentAvailability]


class InsuranceResult(BaseModel):
    """
    Insurance acceptance check result.

    self_pay_rate is populated only when accepted=False, giving the nurse an
    immediate alternative to quote to the patient.
    """
    accepted: bool
    insurance_name: str
    self_pay_rate: Optional[float] = None
    specialty: Optional[str] = None


class AppointmentOutcome(BaseModel):
    """
    Post-appointment outcome record logged by the nurse.

    Outcomes feed back into determine_appointment_type in future sessions:
    a completed outcome counts as an ESTABLISHED visit for the 5-year window.
    """
    outcome_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    session_id: str
    referral_index: int
    provider_name: str
    specialty: str
    location: str
    appointment_date: str
    status: Literal["completed", "no-show", "cancelled"]
    logged_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    nurse_notes: str = ""
