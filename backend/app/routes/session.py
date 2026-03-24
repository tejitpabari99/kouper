from fastapi import APIRouter, HTTPException
from ..session_store import store

router = APIRouter(prefix="/session", tags=["session"])

@router.post("")
def create_session():
    session = store.create()
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

@router.delete("/{session_id}")
def delete_session(session_id: str):
    deleted = store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True, "session_id": session_id}
