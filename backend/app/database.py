"""
SQLite database setup for Kouper Health Care Coordinator.
Single .kouper.db file at the project root; no ORM — raw SQL via sqlite3.
"""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), '../../.kouper.db')


@contextmanager
def get_db():
    """
    Context manager that opens a SQLite connection and ensures it is closed
    after use.  row_factory=sqlite3.Row enables column-name access on results
    (row["session_id"] rather than row[0]).  Foreign key enforcement is
    enabled per-connection since SQLite disables it by default.
    """
    conn = sqlite3.connect(
        os.path.abspath(DB_PATH),
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """
    Create all tables if they do not already exist.  Safe to call on every
    startup — IF NOT EXISTS prevents data loss on re-runs.

    Tables:
      sessions       — one row per nurse workflow session
      bookings       — one row per confirmed referral booking (child of sessions)
      reminders      — patient reminder records tied to a booking
      audit_log      — unified log of API calls, LLM tool calls, and nurse actions
      outcomes       — post-appointment outcome records (completed / no-show / cancelled)
      feedback       — error reports and booking quality ratings from nurses
      local_patients — patients created directly in the UI (not from the EHR API)
    """
    with get_db() as conn:
        conn.executescript("""
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    step TEXT NOT NULL DEFAULT 'patient_lookup',
    insurance TEXT,
    patient JSON,
    selected_provider JSON,
    patient_preferences JSON,
    conversation_history JSON,
    active_referral_index INTEGER NOT NULL DEFAULT 0,
    selected_location_name TEXT,
    appointment_type TEXT
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    referral_index INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    location TEXT NOT NULL,
    appointment_type TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    arrival_minutes_early INTEGER NOT NULL,
    provider_phone TEXT,
    provider_address TEXT,
    provider_hours TEXT,
    nurse_notes TEXT DEFAULT '',
    scheduled_date TEXT,
    booking_confirmed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    booking_referral_index INTEGER NOT NULL,
    touchpoint TEXT NOT NULL,
    channel TEXT NOT NULL,
    contact_value TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    scheduled_for TEXT,
    message_template TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'llm',
    session_id TEXT,
    actor TEXT,
    action TEXT,
    detail JSON,
    tool_name TEXT,
    tool_input JSON,
    tool_output TEXT,
    reasoning_hint TEXT,
    error INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    http_method TEXT,
    http_path TEXT,
    http_status INTEGER,
    duration_ms INTEGER
);

CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    session_id TEXT,
    referral_index INTEGER,
    provider_name TEXT,
    specialty TEXT,
    location TEXT,
    appointment_date TEXT NOT NULL,
    status TEXT NOT NULL,
    nurse_notes TEXT DEFAULT '',
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    data JSON NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS local_patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    pcp TEXT NOT NULL DEFAULT 'Self-referred',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    insurance TEXT,
    ehr_id TEXT NOT NULL,
    referred_specialties JSON NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
        """)
        conn.commit()
