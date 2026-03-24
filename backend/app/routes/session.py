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
