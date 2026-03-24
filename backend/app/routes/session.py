from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..session_store import store
from ..logic.colocated_providers import find_colocated_providers
from ..audit_log import append_audit_entry, AuditLogEntry

router = APIRouter(prefix="/session", tags=["session"])

@router.post("")
def create_session():
    session = store.create()
    append_audit_entry(AuditLogEntry(
        timestamp=datetime.utcnow().isoformat() + "Z",
        type="system", actor="system",
        action="session_created",
        session_id=session.session_id,
    ))
    return {"session_id": session.session_id}

@router.get("/{session_id}/state")
def get_session_state(session_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/by-patient/{patient_id}")
def get_session_by_patient(patient_id: int):
    """Return the most recent session for a patient, if any exists with completed bookings."""
    session = store.get_latest_for_patient(patient_id)
    if not session:
        raise HTTPException(status_code=404, detail="No session found for this patient")
    return {"session_id": session.session_id, "step": session.step, "bookings_count": len(session.bookings)}

@router.get("/{session_id}/colocated-suggestions")
def get_colocated_suggestions(session_id: str):
    """Return co-location suggestions for providers involved in this session's referrals."""
    session = store.get(session_id)
    if not session or not session.patient:
        return []

    # Collect all provider names: from referrals + from confirmed bookings
    provider_names = []
    for ref in session.patient.get("referred_providers", []):
        if ref.get("provider"):
            provider_names.append(ref["provider"])
    for booking in session.bookings:
        provider_names.append(booking.provider_name)

    if len(provider_names) < 2:
        return []

    return find_colocated_providers(provider_names)

@router.get("/{session_id}/reminders")
def get_reminders(session_id: str):
    """Return all scheduled reminder records for this session."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"reminders": [r.model_dump() for r in session.reminders]}


@router.delete("/{session_id}")
def delete_session(session_id: str):
    deleted = store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}
