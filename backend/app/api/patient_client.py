import httpx
from typing import Optional
import os
from dotenv import load_dotenv
from ..models.patient import PatientData
from .exceptions import PatientNotFound, APIUnavailable

load_dotenv('/root/projects/kouper/.env')

PATIENT_API_URL = os.getenv('PATIENT_API_URL', 'http://localhost:5000')

def search_patients(q: str) -> list:
    url = f"{PATIENT_API_URL}/patients"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params={"q": q})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise APIUnavailable(f"Patient search failed: {e}")

def get_patient(patient_id: str | int) -> PatientData:
    """
    Fetch patient data from the Flask API.
    Raises PatientNotFound if 404.
    Raises APIUnavailable if connection fails or 5xx.
    """
    url = f"{PATIENT_API_URL}/patient/{patient_id}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)

        if response.status_code == 404:
            raise PatientNotFound(str(patient_id))

        if response.status_code >= 500:
            raise APIUnavailable(f"API returned {response.status_code}")

        response.raise_for_status()
        data = response.json()
        return PatientData(**data)

    except httpx.ConnectError:
        raise APIUnavailable("Cannot connect to patient API at " + url)
    except httpx.TimeoutException:
        raise APIUnavailable("Patient API request timed out")
    except (PatientNotFound, APIUnavailable):
        raise
    except Exception as e:
        raise APIUnavailable(f"Unexpected error: {e}")
