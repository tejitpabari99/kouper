"""
Integration tests for FastAPI routes using TestClient.
Patient API calls are mocked so no Flask server is required.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.server import app
from app.models.patient import PatientData, ReferredProvider, Appointment
from app.api.exceptions import PatientNotFound

client = TestClient(app)

# Reusable patient fixture data matching the known patient 1
PATIENT_1 = PatientData(
    id=1,
    name="John Doe",
    dob="01/01/1975",
    pcp="Dr. Meredith Grey",
    ehrId="1234abcd",
    referred_providers=[
        ReferredProvider(provider="House, Gregory MD", specialty="Orthopedics"),
        ReferredProvider(specialty="Primary Care"),
    ],
    appointments=[
        Appointment(date="3/05/18", time="9:15am", provider="Dr. Meredith Grey", status="completed"),
        Appointment(date="8/12/24", time="2:30pm", provider="Dr. Gregory House", status="completed"),
        Appointment(date="9/17/24", time="10:00am", provider="Dr. Meredith Grey", status="noshow"),
        Appointment(date="11/25/24", time="11:30am", provider="Dr. Meredith Grey", status="cancelled"),
    ],
)


def _create_session() -> str:
    """Helper: create a session and return its session_id."""
    resp = client.post("/session")
    assert resp.status_code == 200
    return resp.json()["session_id"]


def test_health_check():
    """GET /health → 200 with status ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_create_session():
    """POST /session → 200, response contains session_id."""
    resp = client.post("/session")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0


def test_session_not_found():
    """GET /session/nonexistent/state → 404."""
    resp = client.get("/session/nonexistent-session-id/state")
    assert resp.status_code == 404


def test_start_session_with_valid_patient():
    """POST /session/{id}/start/1 → 200, returns patient data."""
    session_id = _create_session()
    with patch("app.routes.patient.get_patient", return_value=PATIENT_1):
        resp = client.post(f"/session/{session_id}/start/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "John Doe"
    assert data["id"] == 1


def test_start_session_with_invalid_patient():
    """POST /session/{id}/start/999 → 404 when patient not found."""
    session_id = _create_session()
    with patch("app.routes.patient.get_patient", side_effect=PatientNotFound("999")):
        resp = client.post(f"/session/{session_id}/start/999")
    assert resp.status_code == 404


def test_providers_endpoint():
    """GET /providers?specialty=Orthopedics → 200, returns list with House and Brennan."""
    resp = client.get("/providers", params={"specialty": "Orthopedics"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert any("House" in name for name in names)
    assert any("Brennan" in name for name in names)


def test_distance_endpoint():
    """GET /distance → 200, response has miles and drive_minutes."""
    resp = client.get("/distance", params={
        "from_address": "123 Main St",
        "provider_address": "456 Oak Ave",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "miles" in data
    assert "drive_minutes" in data
    assert isinstance(data["miles"], float)
    assert isinstance(data["drive_minutes"], int)


def test_delete_session():
    """Create a session, delete it, then GET it → 404."""
    session_id = _create_session()

    # Confirm session exists
    resp = client.get(f"/session/{session_id}/state")
    assert resp.status_code == 200

    # Delete it
    resp = client.delete(f"/session/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    # Now it should be gone
    resp = client.get(f"/session/{session_id}/state")
    assert resp.status_code == 404


def test_save_preferences():
    """Create session, start with patient 1, save preferences → 200."""
    session_id = _create_session()

    with patch("app.routes.patient.get_patient", return_value=PATIENT_1):
        resp = client.post(f"/session/{session_id}/start/1")
    assert resp.status_code == 200

    prefs_payload = {
        "contact_method": "email",
        "best_contact_time": "afternoon",
        "language": "English",
        "location_preference": "home",
        "transportation_needs": False,
        "notes": "Prefers video calls",
    }
    resp = client.post(f"/session/{session_id}/preferences", json=prefs_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["contact_method"] == "email"
    assert data["language"] == "English"


def test_confirm_booking():
    """Create session, start patient, confirm booking → 200 with booking details."""
    session_id = _create_session()

    with patch("app.routes.patient.get_patient", return_value=PATIENT_1):
        resp = client.post(f"/session/{session_id}/start/1")
    assert resp.status_code == 200

    booking_payload = {
        "referral_index": 0,
        "provider_name": "House, Gregory",
        "specialty": "Orthopedics",
        "location_name": "Jefferson Hospital",
    }
    resp = client.post(f"/session/{session_id}/confirm-booking", json=booking_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider_name"] == "House, Gregory"
    assert data["specialty"] == "Orthopedics"
    assert data["appointment_type"] in ("NEW", "ESTABLISHED")
