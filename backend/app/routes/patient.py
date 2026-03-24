from fastapi import APIRouter, HTTPException, Query
from ..session_store import store
from ..api.patient_client import get_patient, search_patients
from ..api.exceptions import PatientNotFound, APIUnavailable

router = APIRouter(tags=["patient"])

@router.get("/patients")
def search_patients_endpoint(q: str = Query(default="")):
    try:
        return search_patients(q)
    except APIUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

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
        return patient
    except PatientNotFound:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    except APIUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
