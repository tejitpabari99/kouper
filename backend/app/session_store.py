from typing import Dict, Optional
from .models.session import BookingSession

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, BookingSession] = {}

    def create(self) -> BookingSession:
        session = BookingSession()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[BookingSession]:
        return self._sessions.get(session_id)

    def update(self, session: BookingSession) -> BookingSession:
        self._sessions[session.session_id] = session
        return session

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

# Global singleton
store = SessionStore()
