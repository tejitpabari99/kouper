"""
Session persistence layer backed by SQLite.

A BookingSession tracks the entire lifecycle of a nurse's referral booking
workflow for one patient: the loaded patient data, booking progress across
multiple referrals, conversation history, and patient preferences.  This
store handles serialization (Pydantic models → SQLite columns) and
deserialization on reads.
"""
import json
from typing import Optional
from .models.session import BookingSession, CompletedBooking, ReminderRecord
from .database import get_db


class SessionStore:
    def create(self) -> BookingSession:
        """Create a new blank session, persist it, and return it."""
        session = BookingSession()
        self.update(session)
        return session

    def get(self, session_id: str) -> Optional[BookingSession]:
        """
        Load a session and its associated bookings/reminders from SQLite.

        The sessions table stores complex fields (patient dict, conversation
        history, preferences) as JSON blobs that are deserialized here.
        Bookings and reminders live in separate tables and are joined in Python
        rather than via SQL to keep the mapping explicit.

        Returns None if no session with that ID exists.
        """
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row is None:
                return None

            booking_rows = conn.execute(
                "SELECT * FROM bookings WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
            reminder_rows = conn.execute(
                "SELECT * FROM reminders WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()

        session_data = dict(row)

        # Deserialize JSON blobs back into Python objects
        for field in ("patient", "selected_provider", "patient_preferences", "conversation_history"):
            val = session_data.get(field)
            if val is not None:
                session_data[field] = json.loads(val)

        bookings = [CompletedBooking(**dict(r)) for r in booking_rows]
        reminders = [ReminderRecord(**dict(r)) for r in reminder_rows]

        session_data["bookings"] = bookings
        session_data["reminders"] = reminders

        return BookingSession(**session_data)

    def update(self, session: BookingSession) -> BookingSession:
        """
        Persist a session to SQLite using INSERT OR REPLACE (upsert).

        Bookings and reminders are fully replaced on each write (DELETE then
        INSERT) to keep the implementation simple.  This is acceptable at the
        current scale where a session has at most a handful of bookings; a
        diff-based approach would be needed for larger datasets.

        Complex Pydantic fields are serialized to JSON for storage.
        """
        data = session.model_dump()

        # Serialize complex fields to JSON strings for the TEXT/JSON columns
        patient = json.dumps(data.get("patient")) if data.get("patient") is not None else None
        selected_provider = json.dumps(data.get("selected_provider")) if data.get("selected_provider") is not None else None
        patient_preferences = json.dumps(data.get("patient_preferences"), default=str) if data.get("patient_preferences") is not None else None
        conversation_history = json.dumps(data.get("conversation_history", []), default=str)

        created_at = str(data["created_at"])

        with get_db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO sessions
                   (session_id, created_at, step, insurance, patient, selected_provider,
                    patient_preferences, conversation_history, active_referral_index,
                    selected_location_name, appointment_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["session_id"],
                    created_at,
                    data["step"],
                    data.get("insurance"),
                    patient,
                    selected_provider,
                    patient_preferences,
                    conversation_history,
                    data["active_referral_index"],
                    data.get("selected_location_name"),
                    data.get("appointment_type"),
                ),
            )

            # Replace bookings wholesale on every save
            conn.execute("DELETE FROM bookings WHERE session_id = ?", (data["session_id"],))
            for b in data.get("bookings", []):
                conn.execute(
                    """INSERT INTO bookings
                       (session_id, referral_index, provider_name, specialty, location,
                        appointment_type, duration_minutes, arrival_minutes_early,
                        provider_phone, provider_address, provider_hours, nurse_notes,
                        scheduled_date, booking_confirmed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["session_id"],
                        b["referral_index"],
                        b["provider_name"],
                        b["specialty"],
                        b["location"],
                        b["appointment_type"],
                        b["duration_minutes"],
                        b["arrival_minutes_early"],
                        b.get("provider_phone"),
                        b.get("provider_address"),
                        b.get("provider_hours"),
                        b.get("nurse_notes", ""),
                        b.get("scheduled_date"),
                        str(b["booking_confirmed_at"]),
                    ),
                )

            # Replace reminders wholesale on every save
            conn.execute("DELETE FROM reminders WHERE session_id = ?", (data["session_id"],))
            for r in data.get("reminders", []):
                conn.execute(
                    """INSERT INTO reminders
                       (session_id, booking_referral_index, touchpoint, channel,
                        contact_value, status, scheduled_for, message_template)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["session_id"],
                        r["booking_referral_index"],
                        r["touchpoint"],
                        r["channel"],
                        r["contact_value"],
                        r.get("status", "queued"),
                        r.get("scheduled_for"),
                        r["message_template"],
                    ),
                )

            conn.commit()

        return session

    def delete(self, session_id: str) -> bool:
        """Delete a session by ID.  Returns True if the row existed."""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return cur.rowcount > 0

    def get_latest_for_patient(self, patient_id: int) -> Optional[BookingSession]:
        """
        Find the most recent session for a patient that has at least one completed booking.

        Used by the frontend to resume or review a prior session.  Scans all
        sessions (ordered by created_at DESC) and matches on the patient.id
        field stored inside the JSON blob.  Stops at the first session that has
        confirmed bookings.
        """
        with get_db() as conn:
            rows = conn.execute(
                "SELECT session_id, created_at, patient FROM sessions ORDER BY created_at DESC"
            ).fetchall()

        candidates = []
        for row in rows:
            patient_json = row["patient"]
            if patient_json is None:
                continue
            try:
                p = json.loads(patient_json)
                if p.get("id") == patient_id:
                    candidates.append(row)
            except Exception:
                continue

        for row in candidates:
            session = self.get(row["session_id"])
            if session and session.bookings:
                return session

        return None


# Module-level singleton — all routes share one store instance.
store = SessionStore()
