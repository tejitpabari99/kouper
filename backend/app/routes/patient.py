import json
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from ..session_store import store
from ..api.patient_client import get_patient, search_patients
from ..api.exceptions import PatientNotFound, APIUnavailable
from ..audit_log import append_audit_entry, AuditLogEntry
from ..database import get_db
from .new_patient import LOCAL_PATIENT_ID_OFFSET

router = APIRouter(tags=["patient"])

@router.get("/patients")
def search_patients_endpoint(q: str = Query(default="")):
    results = []
    try:
        results = search_patients(q)
    except APIUnavailable:
        pass  # fall through to local results

    # Also search local patients
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM local_patients WHERE LOWER(name) LIKE ? ORDER BY created_at DESC LIMIT 10",
                (f"%{q.lower()}%",),
            ).fetchall()
        for row in rows:
            patient_id = LOCAL_PATIENT_ID_OFFSET + row["id"]
            results.append({
                "id": patient_id,
                "name": row["name"],
                "dob": row["dob"],
                "phone": row["phone"] or "",
                "email": row["email"] or "",
                "ehrId": row["ehr_id"],
                "insurance": row["insurance"],
                "pcp": row["pcp"],
                "is_local": True,
            })
    except Exception:
        pass

    if not results and q:
        raise HTTPException(status_code=503, detail="Patient system unavailable and no local patients found.")
    return results

router2 = APIRouter(prefix="/session", tags=["patient"])

@router2.post("/{session_id}/start/{patient_id}")
def start_session_with_patient(session_id: str, patient_id: int):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        patient = get_patient(patient_id)
        session.patient = patient.model_dump()
        session.step = "referrals_overview"
        store.update(session)
        append_audit_entry(AuditLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            type="system", actor="system",
            action="patient_loaded",
            session_id=session_id,
            detail={"patient_id": str(patient_id), "patient_name": patient.model_dump().get("name", "")},
        ))
        return patient
    except PatientNotFound:
        raise HTTPException(status_code=404, detail="No patient found with that ID. Please verify the patient ID.")
    except APIUnavailable:
        raise HTTPException(status_code=503, detail="The patient information system is temporarily unavailable. Please try again in a moment.")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load patient data. Please try again.")
