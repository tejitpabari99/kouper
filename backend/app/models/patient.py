from pydantic import BaseModel
from typing import List, Literal, Optional


class Appointment(BaseModel):
    date: str        # e.g. "3/05/18" or "8/12/24"
    time: str
    provider: str
    status: str      # completed | noshow | cancelled


class ReferredProvider(BaseModel):
    provider: Optional[str] = None   # None means "unnamed" - just specialty given
    specialty: str
    urgency: Literal["routine", "urgent", "stat"] = "routine"
    priority_note: Optional[str] = None


class PatientData(BaseModel):
    id: int
    name: str
    dob: str
    pcp: str
    ehrId: str
    referred_providers: List[ReferredProvider]
    appointments: List[Appointment]
    insurance: Optional[str] = None
