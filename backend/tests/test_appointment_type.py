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


# A3 — local outcome store integration tests

def test_local_outcome_overrides_no_history():
    """A locally-logged completed outcome within 5 years → ESTABLISHED, even with no EHR history."""
    from app.models.appointment import AppointmentOutcome
    patient = PatientData(
        id=99, name="New Patient", dob="01/01/1990", pcp="Dr. Gregory House",
        ehrId="new001",
        referred_providers=[ReferredProvider(specialty="Orthopedics")],
        appointments=[],
    )
    local_outcomes = [
        AppointmentOutcome(
            patient_id="99", session_id="sess-1", referral_index=0,
            provider_name="Dr. Gregory House", specialty="Orthopedics",
            location="PPTH", appointment_date="2025-06-15", status="completed",
        )
    ]
    result = determine_appointment_type(patient, "Orthopedics", additional_outcomes=local_outcomes)
    assert result.type == "ESTABLISHED"


def test_local_noshows_dont_count():
    """A locally-logged no-show outcome does NOT count toward ESTABLISHED."""
    from app.models.appointment import AppointmentOutcome
    patient = PatientData(
        id=99, name="New Patient", dob="01/01/1990", pcp="Dr. Gregory House",
        ehrId="new002",
        referred_providers=[ReferredProvider(specialty="Orthopedics")],
        appointments=[],
    )
    local_outcomes = [
        AppointmentOutcome(
            patient_id="99", session_id="sess-1", referral_index=0,
            provider_name="Dr. Gregory House", specialty="Orthopedics",
            location="PPTH", appointment_date="2025-06-15", status="no-show",
        )
    ]
    result = determine_appointment_type(patient, "Orthopedics", additional_outcomes=local_outcomes)
    assert result.type == "NEW"


def test_combined_api_and_local_outcomes():
    """Combined: local completed outcome is more recent than EHR; system uses it for ESTABLISHED."""
    from app.models.appointment import AppointmentOutcome
    # Patient's EHR shows a completed Primary Care visit 8 years ago (should give NEW by itself)
    patient = PatientData(
        id=99, name="Combined Test", dob="01/01/1975", pcp="Dr. Meredith Grey",
        ehrId="comb001",
        referred_providers=[ReferredProvider(specialty="Primary Care")],
        appointments=[
            Appointment(date="3/05/18", time="9:15am", provider="Dr. Meredith Grey", status="completed"),
        ],
    )
    # But a local outcome shows a completed Primary Care visit 6 months ago
    local_outcomes = [
        AppointmentOutcome(
            patient_id="99", session_id="sess-2", referral_index=0,
            provider_name="Dr. Meredith Grey", specialty="Primary Care",
            location="PPTH", appointment_date="2025-09-01", status="completed",
        )
    ]
    # Without local outcomes → NEW (EHR date > 5 years)
    result_without = determine_appointment_type(patient, "Primary Care")
    assert result_without.type == "NEW"

    # With local outcomes → ESTABLISHED (local date within 5 years)
    result_with = determine_appointment_type(patient, "Primary Care", additional_outcomes=local_outcomes)
    assert result_with.type == "ESTABLISHED"
