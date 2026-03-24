import json, os
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel

AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), '../../.audit_log.jsonl')

class AuditLogEntry(BaseModel):
    timestamp: str
    type: Literal["api", "system", "llm", "tool", "nurse"] = "llm"
    session_id: Optional[str] = None
    actor: Optional[str] = None           # "nurse", "llm", "system", "api"
    action: Optional[str] = None          # e.g. "booking_confirmed", "step_visited"
    detail: Optional[dict] = None         # free-form context dict
    # LLM/tool fields (Optional now)
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[str] = None
    reasoning_hint: Optional[str] = None
    error: bool = False
    error_code: Optional[str] = None
    # API/timing fields
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    http_status: Optional[int] = None
    duration_ms: Optional[int] = None

def append_audit_entry(entry: AuditLogEntry) -> None:
    """Append one JSON line to the audit log. Silent on any failure."""
    try:
        path = os.path.abspath(AUDIT_LOG_FILE)
        with open(path, 'a') as f:
            f.write(entry.model_dump_json() + '\n')
    except Exception:
        pass  # audit log must never crash the main request path

def get_recent_entries(n: int = 50) -> List[AuditLogEntry]:
    """Return the last n entries from the audit log."""
    try:
        path = os.path.abspath(AUDIT_LOG_FILE)
        if not os.path.exists(path):
            return []
        with open(path, 'r') as f:
            lines = f.readlines()
        entries = []
        for line in lines[-n:]:
            line = line.strip()
            if line:
                try:
                    entries.append(AuditLogEntry(**json.loads(line)))
                except Exception:
                    pass
        return entries
    except Exception:
        return []

def get_entries_filtered(type_filter: Optional[str] = None, n: int = 100) -> List[AuditLogEntry]:
    """Return last n entries, optionally filtered by type."""
    entries = get_recent_entries(n * 3)  # over-fetch then filter
    if type_filter:
        entries = [e for e in entries if e.type == type_filter]
    return entries[-n:]
