"""
Reminder generation logic for confirmed bookings.

Generates three ReminderRecord objects per booking: a booking confirmation,
a 48-hour reminder, and a day-of reminder.  Records are queued (not sent) —
a background job or webhook integration would consume them in production.
"""
from datetime import datetime, date, timedelta
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

    # If booking has a real date, calculate actual reminder dates
    scheduled_date_str = getattr(booking, 'scheduled_date', None)
    if scheduled_date_str:
        try:
            # scheduled_date may be a full ISO datetime string like "2026-04-02T09:00:00"
            appt_date = date.fromisoformat(scheduled_date_str[:10])
            reminder_48h = (appt_date - timedelta(days=2)).isoformat()
            reminder_day_of = appt_date.isoformat()
        except ValueError:
            reminder_48h = "pending_date"
            reminder_day_of = "pending_date"
    else:
        reminder_48h = "pending_date"
        reminder_day_of = "pending_date"

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
            scheduled_for=reminder_48h,
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
            scheduled_for=reminder_day_of,
            message_template=(
                f"Hi {patient_name}, reminder: your appointment with {provider} is today at {location}. "
                f"Arrive {arrive} minutes early."
            ),
        ),
    ]
