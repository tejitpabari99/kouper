from fastapi import APIRouter, HTTPException, Query
from ..session_store import store
from ..logic.slot_generator import generate_slots

router = APIRouter(prefix="/session", tags=["slots"])


@router.get("/{session_id}/appointment-slots")
def get_appointment_slots(
    session_id: str,
    provider: str = Query(...),
    location: str = Query(...),
):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Use 30 min as default duration (safe default for both NEW and ESTABLISHED)
    duration = 30

    groups = generate_slots(provider, location, duration_minutes=duration)
    total_slots = sum(len(g.slots) for g in groups)

    return {
        "provider": provider,
        "location": location,
        "duration_minutes": duration,
        "total_slots": total_slots,
        "slots_by_week": groups,
    }
