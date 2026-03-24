"""
Integration test — requires Flask app running at localhost:5000
Run with: pytest tests/test_patient_api_integration.py -v
Start Flask first: python /root/projects/kouper/MLChallenge/api/flask-app.py
"""
import pytest
from app.api.patient_client import get_patient
from app.api.exceptions import PatientNotFound


def test_get_patient_1_live():
    """Requires Flask running"""
    patient = get_patient(1)
    assert patient.name == "John Doe"
    assert len(patient.referred_providers) == 2


def test_get_patient_not_found_live():
    with pytest.raises(PatientNotFound):
        get_patient(99)
