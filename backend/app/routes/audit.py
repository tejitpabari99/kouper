from fastapi import APIRouter
from ..audit_log import get_recent_entries

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/log")
def get_audit_log(n: int = 50):
    """Return the last n entries from the structured audit log."""
    return get_recent_entries(n)
