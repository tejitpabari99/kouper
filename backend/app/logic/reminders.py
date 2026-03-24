from datetime import datetime
from typing import List, Optional
from ..models.session import CompletedBooking, PatientPreferences, ReminderRecord


def schedule_reminders(
    booking: CompletedBooking,
    preferences: PatientPreferences,
    patient_name: str,
) -> List[ReminderRecord]:
    """
    Generate three reminder records for a confirmed booking.
    Reminders are queued (not actually sent) — caller must persist them.
    """
    channel = preferences.contact_method
    # Build a contact_value from preferences (we don't have real contact info,
    # so use a placeholder that references the preference)
    contact_value = f"via {channel} (contact on file)"

    provider = booking.provider_name
    location = booking.location
    arrive = booking.arrival_minutes_early
    duration = booking.duration_minutes

    now = datetime.utcnow().isoformat() + "Z"

    return [
        ReminderRecord(
            booking_referral_index=booking.referral_index,
            touchpoint="booking_confirmation",
            channel=channel,
            contact_value=contact_value,
            status="queued",
            scheduled_for=now,
            message_template=(
                f"Hi {patient_name}, your referral to {provider} at {location} has been submitted. "
                f"The office will contact you to confirm your appointment date. "
                f"Arrive {arrive} minutes early for your {duration}-minute appointment."
            ),
        ),
        ReminderRecord(
            booking_referral_index=booking.referral_index,
            touchpoint="48hr_reminder",
            channel=channel,
            contact_value=contact_value,
            status="queued",
            scheduled_for="pending_date",
            message_template=(
                f"Hi {patient_name}, you have an appointment with {provider} at {location} in 2 days. "
                f"Please arrive {arrive} minutes early."
            ),
        ),
        ReminderRecord(
            booking_referral_index=booking.referral_index,
            touchpoint="day_of_reminder",
            channel=channel,
            contact_value=contact_value,
            status="queued",
            scheduled_for="pending_date",
            message_template=(
                f"Hi {patient_name}, reminder: your appointment with {provider} is today at {location}. "
                f"Arrive {arrive} minutes early."
            ),
        ),
    ]
