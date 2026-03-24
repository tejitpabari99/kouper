"""
Feedback store — writes error reports and booking feedback to SQLite.
In production, these would be routed to an email/Slack/PagerDuty integration.
"""
import json
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field
import uuid

from .database import get_db


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


def add_feedback(entry: Union[ErrorFeedback, BookingFeedback]) -> None:
    """Insert a feedback entry into SQLite."""
    data = entry.model_dump()
    feedback_type = data.get("type", "unknown")
    created_at = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        conn.execute(
            "INSERT INTO feedback (type, data, created_at) VALUES (?, ?, ?)",
            (feedback_type, json.dumps(data), created_at),
        )
        conn.commit()
