"""
Dispatcher that maps LLM tool-call requests to Python business logic.

When the model decides to use a tool, client.py calls execute_tool() with the
tool name and parsed arguments.  This module resolves each call to the correct
logic function, serializes the result to JSON (the format the Anthropic API
expects as a tool_result), and provides structured error handling so failures
are surfaced gracefully to the nurse without exposing stack traces.
"""
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
    """Machine-readable error codes included in tool error responses.

    The model is instructed to relay only the user_message field to the nurse;
    the code and detail fields are for logging/debugging purposes.
    """
    PATIENT_NOT_FOUND = "PATIENT_NOT_FOUND"
    API_UNAVAILABLE = "API_UNAVAILABLE"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"
    UNKNOWN = "UNKNOWN_ERROR"


def execute_tool(tool_name: str, tool_input: Dict[str, Any], session_patient: Optional[dict] = None) -> str:
    """
    Execute a single LLM tool call and return a JSON string result.

    All tool results — including errors — are returned as JSON strings so the
    Anthropic API can pass them back to the model as tool_result content blocks.

    The lookup_patient tool is intentionally a no-op here: patient data is
    loaded directly by the REST layer before the chat session starts, so the
    model already has patient context in the system prompt.  The tool definition
    still exists so the model can reference the patient_id if needed.

    Args:
        tool_name: Name of the tool the model wants to call.
        tool_input: Dict of arguments the model parsed from the conversation.
        session_patient: The patient dict currently attached to the session,
                         required by determine_appointment_type to access history.

    Returns:
        JSON string — either the tool result or a structured error object.
    """
    try:
        if tool_name == "lookup_patient":
            # Patient loading is handled server-side before the chat starts.
            # The model calls this when asked to look up a patient by ID, but
            # since patient context is already injected via the system prompt,
            # we simply acknowledge the call.
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
            # Reconstruct a typed PatientData so the logic layer can inspect
            # the appointment history list properly.
            patient = PatientData(**session_patient)
            result = determine_appointment_type(patient, tool_input.get("specialty", ""))
            return result.model_dump_json()

        elif tool_name == "check_insurance":
            result = check_insurance(
                tool_input.get("insurance_name", ""),
                tool_input.get("specialty", ""),
                provider_name=tool_input.get("provider_name"),
            )
            return result.model_dump_json()

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    # Structured error handling: each exception type maps to a user-friendly
    # message while preserving technical detail for the audit log.
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
