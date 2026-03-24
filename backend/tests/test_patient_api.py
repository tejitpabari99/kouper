import pytest
from unittest.mock import MagicMock, patch
import httpx

from app.api.patient_client import get_patient
from app.api.exceptions import PatientNotFound, APIUnavailable

PATIENT_1_JSON = {
    "id": 1,
    "name": "John Doe",
    "dob": "01/01/1975",
    "pcp": "Dr. Meredith Grey",
    "ehrId": "1234abcd",
    "referred_providers": [
        {"provider": "House, Gregory MD", "specialty": "Orthopedics"},
        {"specialty": "Primary Care"},
    ],
    "appointments": [
        {"date": "3/05/18", "time": "9:15am", "provider": "Dr. Meredith Grey", "status": "completed"},
        {"date": "8/12/24", "time": "2:30pm", "provider": "Dr. Gregory House", "status": "completed"},
        {"date": "9/17/24", "time": "10:00am", "provider": "Dr. Meredith Grey", "status": "noshow"},
        {"date": "11/25/24", "time": "11:30am", "provider": "Dr. Meredith Grey", "status": "cancelled"},
    ],
}


def make_mock_response(status_code, json_data=None):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    if json_data is not None:
        mock_resp.json.return_value = json_data
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def test_get_patient_success():
    mock_resp = make_mock_response(200, PATIENT_1_JSON)
    with patch("app.api.patient_client.httpx.Client") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_resp

        patient = get_patient(1)

    assert patient.name == "John Doe"
    assert patient.dob == "01/01/1975"
    assert len(patient.referred_providers) == 2
    assert len(patient.appointments) == 4
    assert patient.referred_providers[0].provider == "House, Gregory MD"
    assert patient.referred_providers[1].provider is None
    assert patient.appointments[2].status == "noshow"


def test_get_patient_not_found():
    mock_resp = make_mock_response(404)
    with patch("app.api.patient_client.httpx.Client") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_resp

        with pytest.raises(PatientNotFound):
            get_patient(99)


def test_api_unavailable_500():
    mock_resp = make_mock_response(500)
    with patch("app.api.patient_client.httpx.Client") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_resp

        with pytest.raises(APIUnavailable):
            get_patient(1)


def test_api_unavailable_connection_error():
    with patch("app.api.patient_client.httpx.Client") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(APIUnavailable):
            get_patient(1)


def test_api_unavailable_timeout():
    with patch("app.api.patient_client.httpx.Client") as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timed out")

        with pytest.raises(APIUnavailable):
            get_patient(1)
