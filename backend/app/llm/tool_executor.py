import json
from enum import Enum
from typing import Any, Dict, Optional
from ..logic.provider_search import get_providers
from ..logic.availability import check_availability
from ..logic.insurance import check_insurance
from ..logic.appointment_type import determine_appointment_type
from ..models.patient import PatientData
from ..api.exceptions import PatientNotFound, APIUnavailable


class ErrorCode(str, Enum):
    PATIENT_NOT_FOUND = "PATIENT_NOT_FOUND"
    API_UNAVAILABLE = "API_UNAVAILABLE"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    UNKNOWN = "UNKNOWN_ERROR"


def execute_tool(tool_name: str, tool_input: Dict[str, Any], session_patient: Optional[dict] = None) -> str:
    try:
        if tool_name == "lookup_patient":
            return json.dumps({"note": "lookup_patient handled by server", "patient_id": tool_input.get("patient_id")})

        elif tool_name == "get_providers":
            specialty = tool_input.get("specialty", "")
            providers = get_providers(specialty)
            return json.dumps([{
                "name": f"{p.first_name} {p.last_name}",
                "certification": p.certification,
                "specialty": p.specialty,
                "locations": [{"name": d.name, "phone": d.phone, "address": d.address, "hours": d.hours} for d in p.departments]
            } for p in providers])

        elif tool_name == "check_availability":
            result = check_availability(tool_input.get("provider_name", ""))
            return result.model_dump_json()

        elif tool_name == "determine_appointment_type":
            if not session_patient:
                return json.dumps({"error": "No patient in session"})
            patient = PatientData(**session_patient)
            result = determine_appointment_type(patient, tool_input.get("specialty", ""))
            return result.model_dump_json()

        elif tool_name == "check_insurance":
            result = check_insurance(tool_input.get("insurance_name", ""), tool_input.get("specialty", ""))
            return result.model_dump_json()

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except PatientNotFound as e:
        return json.dumps({
            "error": True,
            "code": ErrorCode.PATIENT_NOT_FOUND.value,
            "user_message": "No patient record found with that ID. Please verify and try again.",
            "detail": str(e),
        })
    except APIUnavailable as e:
        return json.dumps({
            "error": True,
            "code": ErrorCode.API_UNAVAILABLE.value,
            "user_message": "The patient information system is temporarily unavailable. Please try again in a moment.",
            "detail": str(e),
        })
    except ValueError as e:
        if "not found" in str(e).lower():
            return json.dumps({
                "error": True,
                "code": ErrorCode.PROVIDER_NOT_FOUND.value,
                "user_message": "That provider was not found in the system. The name may be spelled differently.",
                "detail": str(e),
            })
        return json.dumps({
            "error": True,
            "code": ErrorCode.INVALID_INPUT.value,
            "user_message": "The assistant encountered an unexpected error processing your request. Please try again.",
            "detail": str(e),
        })
    except Exception as e:
        return json.dumps({
            "error": True,
            "code": ErrorCode.UNKNOWN.value,
            "user_message": "The assistant encountered an unexpected error processing your request. Please try again.",
            "detail": str(e),
        })
