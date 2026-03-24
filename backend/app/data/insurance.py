ACCEPTED_INSURANCES = [
    "Medicaid",
    "United Health Care",
    "Blue Cross Blue Shield of North Carolina",
    "Aetna",
    "Cigna",
]

SELF_PAY_RATES = {
    "Primary Care": 150.0,
    "Orthopedics": 300.0,
    "Surgery": 1000.0,
}

PRIOR_AUTH_REQUIRED = {
    ("Surgery", "Cigna"): True,
    ("Surgery", "United Health Care"): True,
    ("Orthopedics", "Aetna"): True,
    ("Orthopedics", "United Health Care"): True,
}
