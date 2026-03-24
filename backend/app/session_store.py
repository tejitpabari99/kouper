import json
import os
from typing import Dict, Optional
from .models.session import BookingSession

SESSIONS_FILE = os.path.join(os.path.dirname(__file__), '../../.sessions.json')

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, BookingSession] = {}
        self._load()

    def _load(self):
        try:
            path = os.path.abspath(SESSIONS_FILE)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                for sid, raw in data.items():
                    try:
                        self._sessions[sid] = BookingSession(**raw)
                    except Exception:
                        pass  # skip malformed sessions
        except Exception:
            pass

    def _save(self):
        try:
            path = os.path.abspath(SESSIONS_FILE)
            data = {sid: s.model_dump() for sid, s in self._sessions.items()}
            with open(path, 'w') as f:
                json.dump(data, f, default=str)
        except Exception:
            pass

    def create(self) -> BookingSession:
        session = BookingSession()
        self._sessions[session.session_id] = session
        self._save()
        return session

    def get(self, session_id: str) -> Optional[BookingSession]:
        return self._sessions.get(session_id)

    def update(self, session: BookingSession) -> BookingSession:
        self._sessions[session.session_id] = session
        self._save()
        return session

    def get_latest_for_patient(self, patient_id: int) -> Optional[BookingSession]:
        """Return the most recent session that has this patient loaded and has bookings."""
        matches = [
            s for s in self._sessions.values()
            if isinstance(s.patient, dict) and s.patient.get('id') == patient_id and s.bookings
        ]
        if not matches:
            return None
        return max(matches, key=lambda s: s.created_at if hasattr(s, 'created_at') else s.session_id)

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save()
            return True
        return False

# Global singleton
store = SessionStore()
