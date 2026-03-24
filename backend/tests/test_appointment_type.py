import pytest
from app.models.patient import PatientData, ReferredProvider, Appointment
from app.logic.appointment_type import determine_appointment_type

JOHN_DOE = PatientData(
    id=1, name="John Doe", dob="01/01/1975", pcp="Dr. Meredith Grey", ehrId="1234abcd",
    referred_providers=[
        ReferredProvider(provider="House, Gregory MD", specialty="Orthopedics"),
        ReferredProvider(specialty="Primary Care"),
    ],
    appointments=[
        Appointment(date="3/05/18", time="9:15am", provider="Dr. Meredith Grey", status="completed"),
        Appointment(date="8/12/24", time="2:30pm", provider="Dr. Gregory House", status="completed"),
        Appointment(date="9/17/24", time="10:00am", provider="Dr. Meredith Grey", status="noshow"),
        Appointment(date="11/25/24", time="11:30am", provider="Dr. Meredith Grey", status="cancelled"),
    ]
)


def test_appointment_type_orthopedics_established():
    """House appointment 8/12/2024 is within 5 years → ESTABLISHED."""
    result = determine_appointment_type(JOHN_DOE, "Orthopedics")
    assert result.type == "ESTABLISHED"
    assert result.duration_minutes == 15
    assert result.arrival_minutes_early == 10


def test_appointment_type_primary_care_new():
    """Grey's only completed appointment was 3/5/2018 (> 5 years ago) → NEW."""
    result = determine_appointment_type(JOHN_DOE, "Primary Care")
    assert result.type == "NEW"
    assert result.duration_minutes == 30
    assert result.arrival_minutes_early == 30


def test_noshows_dont_count():
    """Grey's noshow on 9/17/2024 should not count; result is still NEW."""
    result = determine_appointment_type(JOHN_DOE, "Primary Care")
    assert result.type == "NEW"


def test_cancellations_dont_count():
    """Grey's cancellation on 11/25/2024 should not count; result is still NEW."""
    result = determine_appointment_type(JOHN_DOE, "Primary Care")
    assert result.type == "NEW"
