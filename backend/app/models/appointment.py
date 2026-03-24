from pydantic import BaseModel, Field
from typing import Literal, List, Optional
import uuid
from datetime import datetime


class AppointmentTypeResult(BaseModel):
    type: Literal["NEW", "ESTABLISHED"]
    duration_minutes: int       # NEW=30, ESTABLISHED=15
    arrival_minutes_early: int  # NEW=30, ESTABLISHED=10
    reason: str                 # Human-readable explanation


class DepartmentAvailability(BaseModel):
    department_name: str
    days: List[str]     # e.g. ["Monday", "Tuesday", "Wednesday"]
    hours: str          # e.g. "9am-5pm"
    phone: str
    address: str


class AvailabilityResult(BaseModel):
    provider_name: str
    specialty: str
    locations: List[DepartmentAvailability]


class InsuranceResult(BaseModel):
    accepted: bool
    insurance_name: str
    self_pay_rate: Optional[float] = None
    specialty: Optional[str] = None


class AppointmentOutcome(BaseModel):
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
