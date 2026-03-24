"""
Persistent store for appointment outcomes backed by SQLite.
"""
from typing import List
from datetime import datetime

from .models.appointment import AppointmentOutcome
from .database import get_db


def add_outcome(outcome: AppointmentOutcome) -> None:
    data = outcome.model_dump()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO outcomes
               (patient_id, session_id, referral_index, provider_name, specialty,
                location, appointment_date, status, nurse_notes, recorded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["patient_id"],
                data.get("session_id"),
                data.get("referral_index"),
                data.get("provider_name"),
                data.get("specialty"),
                data.get("location"),
                data["appointment_date"],
                data["status"],
                data.get("nurse_notes", ""),
                data.get("logged_at", datetime.utcnow().isoformat() + "Z"),
            ),
        )
        conn.commit()


def get_outcomes_for_patient(patient_id) -> List[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM outcomes WHERE patient_id = ? ORDER BY recorded_at DESC",
            (str(patient_id),),
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_outcomes() -> List[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM outcomes ORDER BY recorded_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]
