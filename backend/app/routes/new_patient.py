import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..database import get_db
from ..session_store import store
from ..models.patient import PatientData, ReferredProvider
from ..audit_log import append_audit_entry, AuditLogEntry

router = APIRouter(tags=["new_patient"])

LOCAL_PATIENT_ID_OFFSET = 10000  # avoid collisions with ML Challenge IDs


class NewPatientRequest(BaseModel):
    name: str
    dob: str
    pcp: str = "Self-referred"
    phone: str = ""
    email: str = ""
    insurance: Optional[str] = None
    referred_specialties: List[str] = []  # e.g. ["Orthopedics", "Primary Care"]


@router.post("/patients/local")
def create_local_patient(body: NewPatientRequest):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Patient name is required.")
    if not body.dob.strip():
        raise HTTPException(status_code=400, detail="Date of birth is required.")
    if not body.referred_specialties:
        raise HTTPException(status_code=400, detail="At least one referral specialty is required.")

    created_at = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO local_patients (name, dob, pcp, phone, email, insurance, ehr_id, referred_specialties, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                body.name.strip(),
                body.dob.strip(),
                body.pcp.strip() or "Self-referred",
                body.phone.strip(),
                body.email.strip(),
                body.insurance,
                "",  # placeholder, set after we have the id
                json.dumps(body.referred_specialties),
                created_at,
            ),
        )
        patient_id = LOCAL_PATIENT_ID_OFFSET + cur.lastrowid
        ehr_id = f"LOCAL-{patient_id}"
        conn.execute("UPDATE local_patients SET ehr_id = ? WHERE id = ?", (ehr_id, cur.lastrowid))
        conn.commit()

    patient_dict = {
        "id": patient_id,
        "name": body.name.strip(),
        "dob": body.dob.strip(),
        "pcp": body.pcp.strip() or "Self-referred",
        "phone": body.phone.strip(),
        "email": body.email.strip(),
        "insurance": body.insurance,
        "ehrId": ehr_id,
        "referred_providers": [
            {"specialty": s, "provider": None, "urgency": "routine"}
            for s in body.referred_specialties
        ],
        "appointments": [],
    }

    append_audit_entry(AuditLogEntry(
        timestamp=created_at,
        type="system", actor="nurse",
        action="local_patient_created",
        detail={"patient_id": patient_id, "name": body.name.strip()},
    ))

    return patient_dict


@router.get("/patients/local")
def search_local_patients(q: str = ""):
    """Search locally-created patients by name."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM local_patients WHERE LOWER(name) LIKE ? ORDER BY created_at DESC LIMIT 20",
            (f"%{q.lower()}%",),
        ).fetchall()

    results = []
    for row in rows:
        patient_id = LOCAL_PATIENT_ID_OFFSET + row["id"]
        results.append({
            "id": patient_id,
            "name": row["name"],
            "dob": row["dob"],
            "phone": row["phone"],
            "email": row["email"],
            "ehrId": row["ehr_id"],
            "insurance": row["insurance"],
            "referred_providers": [
                {"specialty": s, "provider": None, "urgency": "routine"}
                for s in json.loads(row["referred_specialties"] or "[]")
            ],
            "appointments": [],
            "pcp": row["pcp"],
            "is_local": True,
        })
    return results


@router.post("/session/{session_id}/start-local/{patient_id}")
def start_session_with_local_patient(session_id: str, patient_id: int):
    """Start a session using a locally-created patient."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db_id = patient_id - LOCAL_PATIENT_ID_OFFSET
    if db_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid local patient ID")

    with get_db() as conn:
        row = conn.execute("SELECT * FROM local_patients WHERE id = ?", (db_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Local patient not found")

    patient_dict = {
        "id": patient_id,
        "name": row["name"],
        "dob": row["dob"],
        "pcp": row["pcp"],
        "phone": row["phone"],
        "email": row["email"],
        "insurance": row["insurance"],
        "ehrId": row["ehr_id"],
        "referred_providers": [
            {"specialty": s, "provider": None, "urgency": "routine"}
            for s in json.loads(row["referred_specialties"] or "[]")
        ],
        "appointments": [],
    }

    session.patient = patient_dict
    session.step = "referrals_overview"
    store.update(session)

    append_audit_entry(AuditLogEntry(
        timestamp=datetime.utcnow().isoformat() + "Z",
        type="system", actor="system",
        action="local_patient_loaded",
        session_id=session_id,
        detail={"patient_id": patient_id, "patient_name": row["name"]},
    ))

    return patient_dict
