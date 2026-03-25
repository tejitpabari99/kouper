"""
Feedback collection routes for error reports and booking quality ratings.

Two feedback types are supported:
  - Error feedback: nurse-reported errors with an incident ID for support tracking
  - Booking feedback: 1–5 star rating with comment after a booking is completed

In production these would trigger notifications (PagerDuty/Slack for errors,
email digest for booking quality).  Currently stored locally in SQLite.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ..feedback_store import ErrorFeedback, BookingFeedback, add_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


class ErrorFeedbackRequest(BaseModel):
    incident_id: str
    error_code: Optional[str] = None
    error_message: str
    session_id: Optional[str] = None
    page_context: Optional[str] = None
    user_comment: str = ""


class BookingFeedbackRequest(BaseModel):
    session_id: str
    referral_index: int
    provider_name: str
    specialty: str
    rating: int
    comment: str = ""


@router.post("/error")
def submit_error_feedback(body: ErrorFeedbackRequest):
    entry = ErrorFeedback(**body.model_dump())
    add_feedback(entry)
    return {
        "recorded": True,
        "incident_id": entry.incident_id,
        "note": "Feedback stored locally. In production, this would notify the engineering team via PagerDuty / Slack.",
    }


@router.post("/booking")
def submit_booking_feedback(body: BookingFeedbackRequest):
    entry = BookingFeedback(**body.model_dump())
    add_feedback(entry)
    return {
        "recorded": True,
        "feedback_id": entry.feedback_id,
        "note": "Feedback stored locally. In production, this would be emailed to the care quality team.",
    }
