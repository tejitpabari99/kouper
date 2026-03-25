"""
Send booking summary route (stub).

In production this would dispatch an SMS or email to the patient with their
appointment details.  Currently returns a mock success response — the
Twilio/SendGrid integration is not yet connected.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..session_store import store

router = APIRouter(prefix="/session", tags=["send_summary"])

class SendSummaryRequest(BaseModel):
    method: str  # "text" or "email"
    contact: str = ""  # phone number or email address

@router.post("/{session_id}/send-summary")
def send_summary(session_id: str, body: SendSummaryRequest):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "sent": True,
        "method": body.method,
        "contact": body.contact,
        "message": f"Summary {'text message' if body.method == 'text' else 'email'} queued successfully.",
        "note": "Mock only — SMS/email integration (Twilio/SendGrid) not yet connected."
    }
