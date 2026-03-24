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
