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


def test_patient_with_no_appointment_history():
    """A patient with an empty appointments list should always be NEW."""
    patient = PatientData(
        id=2, name="Jane Smith", dob="06/15/1990", pcp="Dr. Chris Perry",
        ehrId="5678efgh",
        referred_providers=[ReferredProvider(specialty="Primary Care")],
        appointments=[],
    )
    result = determine_appointment_type(patient, "Primary Care")
    assert result.type == "NEW"
    assert result.duration_minutes == 30
    assert result.arrival_minutes_early == 30


def test_appointment_type_surgery():
    """A patient with no surgical history should be NEW for Surgery."""
    patient = PatientData(
        id=3, name="Bob Builder", dob="03/20/1980", pcp="Dr. Meredith Grey",
        ehrId="9012ijkl",
        referred_providers=[ReferredProvider(specialty="Surgery")],
        appointments=[
            Appointment(date="8/12/24", time="2:30pm", provider="Dr. Gregory House", status="completed"),
        ],
    )
    result = determine_appointment_type(patient, "Surgery")
    assert result.type == "NEW"


def test_only_completed_count_for_established():
    """A patient with a completed visit to Grey within 5 years should be ESTABLISHED for Primary Care."""
    patient = PatientData(
        id=4, name="Alice Walker", dob="09/10/1985", pcp="Dr. Meredith Grey",
        ehrId="3456mnop",
        referred_providers=[ReferredProvider(specialty="Primary Care")],
        appointments=[
            # Completed Primary Care visit within 5 years (2024 is within 5 years of 2026-03-24)
            Appointment(date="5/10/24", time="10:00am", provider="Dr. Meredith Grey", status="completed"),
            # Noshow should not affect outcome
            Appointment(date="11/15/24", time="9:00am", provider="Dr. Meredith Grey", status="noshow"),
        ],
    )
    result = determine_appointment_type(patient, "Primary Care")
    assert result.type == "ESTABLISHED"
