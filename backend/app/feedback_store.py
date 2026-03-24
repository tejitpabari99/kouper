"""
Feedback store — writes error reports and booking feedback to .feedback.json.
In production, these would be routed to an email/Slack/PagerDuty integration.
"""
import json
import os
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid

FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "../../.feedback.json")


class ErrorFeedback(BaseModel):
    incident_id: str
    type: str = "error_report"
    error_code: Optional[str] = None
    error_message: str
    session_id: Optional[str] = None
    page_context: Optional[str] = None
    user_comment: str = ""
    logged_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class BookingFeedback(BaseModel):
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "booking_feedback"
    session_id: str
    referral_index: int
    provider_name: str
    specialty: str
    rating: int           # 1–5 stars
    comment: str = ""
    logged_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


def _load() -> list:
    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(entries: list) -> None:
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def add_feedback(entry: ErrorFeedback | BookingFeedback) -> None:
    entries = _load()
    entries.append(entry.model_dump())
    _save(entries)
