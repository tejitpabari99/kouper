from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from ..session_store import store
from ..models.session import PatientPreferences
from ..audit_log import append_audit_entry, AuditLogEntry

router = APIRouter(prefix="/session", tags=["preferences"])

class PreferencesRequest(BaseModel):
    contact_method: Literal["phone", "text", "email"] = "phone"
    best_contact_time: str = "morning"
    language: str = "English"
    location_preference: Literal["home", "work", "none"] = "none"
    transportation_needs: bool = False
    notes: str = ""

@router.post("/{session_id}/preferences")
def save_preferences(session_id: str, body: PreferencesRequest):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.patient:
        raise HTTPException(status_code=400, detail="No patient loaded in session")

    prefs = PatientPreferences(
        patient_id=str(session.patient["id"]),
        contact_method=body.contact_method,
        best_contact_time=body.best_contact_time,
        language=body.language,
        location_preference=body.location_preference,
        transportation_needs=body.transportation_needs,
        notes=body.notes,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.patient_preferences = prefs
    store.update(session)
    append_audit_entry(AuditLogEntry(
        timestamp=datetime.utcnow().isoformat() + "Z",
        type="system", actor="system",
        action="preferences_saved",
        session_id=session_id,
        detail={"contact_method": body.contact_method, "transportation_needs": body.transportation_needs},
    ))
    return prefs
