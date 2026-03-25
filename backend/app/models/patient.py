"""
Patient data models sourced from the MLChallenge Flask API.

PatientData is the canonical representation of a patient used throughout
the backend.  It is loaded from the external API and stored as a JSON dict
in the session; use PatientData(**session.patient) to get a typed object.
"""
from pydantic import BaseModel
from typing import List, Literal, Optional


class Appointment(BaseModel):
    """Historical appointment record.  status drives NEW vs. ESTABLISHED logic."""
    date: str        # e.g. "3/05/18" or "8/12/24"
    time: str
    provider: str
    status: str      # completed | noshow | cancelled


class ReferredProvider(BaseModel):
    """
    A single referral on a patient's discharge order.

    provider may be None when the discharge order specifies only a specialty
    without naming a specific provider — the nurse then selects one.
    """
    provider: Optional[str] = None   # None means "unnamed" - just specialty given
    specialty: str
    urgency: Literal["routine", "urgent", "stat"] = "routine"
    priority_note: Optional[str] = None


class PatientData(BaseModel):
    """Full patient record as returned by the MLChallenge patient API."""
    id: int
    name: str
    dob: str
    pcp: str
    ehrId: str
    referred_providers: List[ReferredProvider]
    appointments: List[Appointment]  # Full history including no-shows and cancellations
    insurance: Optional[str] = None
