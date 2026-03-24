import json
from typing import Any, Dict, Optional
from ..logic.provider_search import get_providers
from ..logic.availability import check_availability
from ..logic.insurance import check_insurance
from ..logic.appointment_type import determine_appointment_type
from ..models.patient import PatientData

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
    except Exception as e:
        return json.dumps({"error": str(e), "tool": tool_name})
