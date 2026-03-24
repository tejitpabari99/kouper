from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..audit_log import get_recent_entries, get_entries_filtered, append_audit_entry, AuditLogEntry

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/log")
def get_audit_log(n: int = 100, type: Optional[str] = None):
    """Return the last n entries from the structured audit log, optionally filtered by type."""
    return get_entries_filtered(type_filter=type, n=n)

class NurseEventRequest(BaseModel):
    session_id: Optional[str] = None
    action: str
    detail: dict = {}

@router.post("/event")
def log_nurse_event(body: NurseEventRequest):
    """Record a nurse-side UI action in the audit log."""
    append_audit_entry(AuditLogEntry(
        timestamp=datetime.utcnow().isoformat() + "Z",
        type="nurse",
        actor="nurse",
        session_id=body.session_id,
        action=body.action,
        detail=body.detail,
    ))
    return {"logged": True}
