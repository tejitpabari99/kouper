import json
import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), '../../.audit_log.jsonl')

class AuditLogEntry(BaseModel):
    timestamp: str
    session_id: str
    tool_name: str
    tool_input: dict
    tool_output: str         # raw JSON string returned by tool
    reasoning_hint: str      # LLM text blocks before tool call
    error: bool = False
    error_code: Optional[str] = None

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
