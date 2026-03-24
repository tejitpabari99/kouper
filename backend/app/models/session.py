from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid


class PatientPreferences(BaseModel):
    patient_id: str
    contact_method: Literal["phone", "text", "email"] = "phone"
    best_contact_time: str = "morning"
    language: str = "English"
    location_preference: Literal["home", "work", "none"] = "none"
    transportation_needs: bool = False
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_nurse_id: Optional[str] = None


class CompletedBooking(BaseModel):
    referral_index: int
    provider_name: str
    specialty: str
    location: str
    appointment_type: str     # NEW or ESTABLISHED
    duration_minutes: int
    arrival_minutes_early: int
    provider_phone: Optional[str] = None
    provider_address: Optional[str] = None
    provider_hours: Optional[str] = None
    booking_confirmed_at: datetime = Field(default_factory=datetime.now)
    nurse_notes: str = ""
    scheduled_date: Optional[str] = None


class ReminderRecord(BaseModel):
    booking_referral_index: int
    touchpoint: Literal["booking_confirmation", "48hr_reminder", "day_of_reminder"]
    channel: str            # mirrors PatientPreferences.contact_method
    contact_value: str      # phone number or email — from preferences
    status: Literal["queued", "sent", "failed"] = "queued"
    scheduled_for: Optional[str] = None   # ISO date string or "pending_date"
    message_template: str   # the fully rendered reminder text


class BookingSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    step: str = "patient_lookup"
    # Steps: patient_lookup | referrals_overview | provider_selection | appointment_details | preferences | confirmation | complete
    patient: Optional[dict] = None  # PatientData as dict to avoid circular imports
    active_referral_index: int = 0
    bookings: List[CompletedBooking] = []
    selected_provider: Optional[dict] = None
    appointment_type: Optional[str] = None
    selected_location_name: Optional[str] = None
    patient_preferences: Optional[PatientPreferences] = None
    conversation_history: List[dict] = []
    reminders: List[ReminderRecord] = []
