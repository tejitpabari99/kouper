"""
Core session data models for the care coordinator booking workflow.

These Pydantic models are the schema for what gets persisted to SQLite and
what the LLM and frontend interact with at runtime.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import uuid


class PatientPreferences(BaseModel):
    """Patient communication and logistics preferences collected by the nurse."""
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
    """
    A confirmed referral booking within a session.

    referral_index maps back to the patient's referred_providers list so the
    frontend knows which referral slot this booking fulfills.
    appointment_type (NEW/ESTABLISHED) determines duration and arrival instructions.
    """
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
    """
    A queued patient reminder associated with a specific booking.

    Three touchpoints are generated per booking: booking confirmation,
    48-hour reminder, and day-of reminder.  In production these would be
    dispatched via SMS/email; currently they are stored as queued records.
    """
    booking_referral_index: int
    touchpoint: Literal["booking_confirmation", "48hr_reminder", "day_of_reminder"]
    channel: str            # mirrors PatientPreferences.contact_method
    contact_value: str      # phone number or email — from preferences
    status: Literal["queued", "sent", "failed"] = "queued"
    scheduled_for: Optional[str] = None   # ISO date string or "pending_date"
    message_template: str   # the fully rendered reminder text


class BookingSession(BaseModel):
    """
    Root model for a nurse's end-to-end booking workflow for one patient.

    Tracks everything needed to resume mid-session: which patient is loaded,
    which referrals have been booked, the LLM conversation history, and the
    nurse-collected patient preferences.

    Steps: patient_lookup | referrals_overview | provider_selection |
           appointment_details | preferences | confirmation | complete
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    step: str = "patient_lookup"
    patient: Optional[dict] = None  # PatientData as dict to avoid circular imports
    active_referral_index: int = 0
    bookings: List[CompletedBooking] = []
    selected_provider: Optional[dict] = None
    appointment_type: Optional[str] = None
    selected_location_name: Optional[str] = None
    patient_preferences: Optional[PatientPreferences] = None
    conversation_history: List[dict] = []  # Anthropic message format [{role, content}]
    reminders: List[ReminderRecord] = []
    insurance: Optional[str] = None  # nurse-entered insurance, overrides patient EHR data
