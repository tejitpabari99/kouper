import json
from typing import List, Literal, Optional
from pydantic import BaseModel
from .database import get_db


class AuditLogEntry(BaseModel):
    timestamp: str
    type: Literal["api", "system", "llm", "tool", "nurse"] = "llm"
    session_id: Optional[str] = None
    actor: Optional[str] = None
    action: Optional[str] = None
    detail: Optional[dict] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[str] = None
    reasoning_hint: Optional[str] = None
    error: bool = False
    error_code: Optional[str] = None
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    http_status: Optional[int] = None
    duration_ms: Optional[int] = None


def append_audit_entry(entry: AuditLogEntry) -> None:
    """Insert one audit log entry into the database. Silent on any failure."""
    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO audit_log
                   (timestamp, type, session_id, actor, action, detail,
                    tool_name, tool_input, tool_output, reasoning_hint,
                    error, error_code, http_method, http_path, http_status, duration_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.timestamp,
                    entry.type,
                    entry.session_id,
                    entry.actor,
                    entry.action,
                    json.dumps(entry.detail) if entry.detail is not None else None,
                    entry.tool_name,
                    json.dumps(entry.tool_input) if entry.tool_input is not None else None,
                    entry.tool_output,
                    entry.reasoning_hint,
                    1 if entry.error else 0,
                    entry.error_code,
                    entry.http_method,
                    entry.http_path,
                    entry.http_status,
                    entry.duration_ms,
                ),
            )
            conn.commit()
    except Exception:
        pass  # audit log must never crash the main request path


def get_entries_filtered(type_filter: Optional[str] = None, n: int = 100) -> List[dict]:
    """Return last n entries from audit_log, optionally filtered by type. Returns list of dicts."""
    try:
        with get_db() as conn:
            if type_filter:
                rows = conn.execute(
                    "SELECT * FROM audit_log WHERE type = ? ORDER BY id DESC LIMIT ?",
                    (type_filter, n),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
                    (n,),
                ).fetchall()

        results = []
        for row in rows:
            d = dict(row)
            # Parse JSON fields
            if d.get("detail") is not None:
                try:
                    d["detail"] = json.loads(d["detail"])
                except Exception:
                    pass
            if d.get("tool_input") is not None:
                try:
                    d["tool_input"] = json.loads(d["tool_input"])
                except Exception:
                    pass
            # Convert error int back to bool
            d["error"] = bool(d.get("error", 0))
            results.append(d)
        return results
    except Exception:
        return []


def get_recent_entries(n: int = 50) -> List[AuditLogEntry]:
    """Return the last n entries from the audit log as AuditLogEntry objects."""
    try:
        rows = get_entries_filtered(type_filter=None, n=n)
        entries = []
        for d in rows:
            try:
                entries.append(AuditLogEntry(**d))
            except Exception:
                pass
        return entries
    except Exception:
        return []
