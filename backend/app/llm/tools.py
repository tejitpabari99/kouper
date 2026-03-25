"""
Tool definitions exposed to the LLM as function-calling capabilities.

Each entry in TOOLS follows the Anthropic tool-use schema and maps to a
concrete Python handler in tool_executor.py.  The description field is
what the model reads to decide when and how to call each tool — wording
matters for correct tool selection.
"""

# These five tools represent the core "skills" the assistant needs to guide
# a nurse through the post-discharge referral booking workflow:
#   lookup_patient  → identify the patient and load their EHR data
#   get_providers   → find specialists for a referral
#   check_availability  → know when/where a provider can see patients
#   determine_appointment_type  → decide NEW vs ESTABLISHED (affects duration/arrival)
#   check_insurance  → verify coverage and surface self-pay cost if rejected
TOOLS = [
    {
        "name": "lookup_patient",
        "description": "Load a patient's complete record from the patient API by their ID.",
        "input_schema": {"type": "object", "properties": {"patient_id": {"type": "string"}}, "required": ["patient_id"]}
    },
    {
        "name": "get_providers",
        "description": "Find all available providers for a given medical specialty.",
        "input_schema": {"type": "object", "properties": {"specialty": {"type": "string", "description": "e.g. 'Primary Care', 'Orthopedics', 'Surgery'"}}, "required": ["specialty"]}
    },
    {
        "name": "check_availability",
        "description": "Check a provider's available days, hours, and locations.",
        "input_schema": {"type": "object", "properties": {"provider_name": {"type": "string"}}, "required": ["provider_name"]}
    },
    {
        "name": "determine_appointment_type",
        # The model calls this before quoting appointment duration or arrival instructions.
        # It uses the patient's appointment history (already in session context) to
        # apply the 5-year ESTABLISHED rule without the model having to reason about it.
        "description": "Determine whether a patient needs a NEW or ESTABLISHED appointment for a given specialty based on their history.",
        "input_schema": {"type": "object", "properties": {"specialty": {"type": "string"}}, "required": ["specialty"]}
    },
    {
        "name": "check_insurance",
        "description": "Check whether an insurance is accepted. If not, returns self-pay rate for the specialty.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insurance_name": {"type": "string"},
                "specialty": {"type": "string", "description": "For self-pay rate if insurance rejected"}
            },
            "required": ["insurance_name"]
        }
    },
]
