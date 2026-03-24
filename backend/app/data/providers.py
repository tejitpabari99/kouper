from typing import List
from app.models.provider import Provider, Department

PROVIDERS: List[Provider] = [
    Provider(
        last_name="Grey",
        first_name="Meredith",
        certification="MD",
        specialty="Primary Care",
        accepted_insurances=["Medicaid", "United Health Care", "Blue Cross Blue Shield of North Carolina", "Aetna", "Cigna", "Blue Cross Blue Shield"],
        accepting_new_patients=True,
        departments=[
            Department(
                name="Sloan Primary Care",
                phone="(710) 555-2070",
                address="202 Maple St, Winston-Salem, NC 27101",
                hours="M-F 9am-5pm",
            )
        ],
    ),
    Provider(
        last_name="House",
        first_name="Gregory",
        certification="MD",
        specialty="Orthopedics",
        accepted_insurances=["Blue Cross Blue Shield of North Carolina", "Blue Cross Blue Shield", "Aetna", "United Health Care"],
        accepting_new_patients=True,
        departments=[
            Department(
                name="PPTH Orthopedics",
                phone="(445) 555-6205",
                address="101 Pine St, Greensboro, NC 27401",
                hours="M-W 9am-5pm",
            ),
            Department(
                name="Jefferson Hospital",
                phone="(215) 555-6123",
                address="202 Maple St, Claremont, NC 28610",
                hours="Th-F 9am-5pm",
            ),
        ],
    ),
    Provider(
        last_name="Yang",
        first_name="Cristina",
        certification="MD",
        specialty="Surgery",
        accepted_insurances=["Medicaid", "Aetna", "Cigna"],
        accepting_new_patients=False,
        waitlist_available=True,
        departments=[
            Department(
                name="Seattle Grace Cardiac Surgery",
                phone="(710) 555-3082",
                address="456 Elm St, Charlotte, NC 28202",
                hours="M-F 9am-5pm",
            )
        ],
    ),
    Provider(
        last_name="Perry",
        first_name="Chris",
        certification="FNP",
        specialty="Primary Care",
        accepted_insurances=["Medicaid", "United Health Care", "Blue Cross Blue Shield of North Carolina", "Blue Cross Blue Shield"],
        accepting_new_patients=True,
        departments=[
            Department(
                name="Sacred Heart Surgical Department",
                phone="(339) 555-7480",
                address="123 Main St, Raleigh, NC 27601",
                hours="M-W 9am-5pm",
            )
        ],
    ),
    Provider(
        last_name="Brennan",
        first_name="Temperance",
        certification="PhD, MD",
        specialty="Orthopedics",
        accepted_insurances=["Aetna", "Cigna", "United Health Care"],
        accepting_new_patients=True,
        departments=[
            Department(
                name="Jefferson Hospital",
                phone="(215) 555-6123",
                address="202 Maple St, Claremont, NC 28610",
                hours="Tu-Th 10am-4pm",
            )
        ],
    ),
]
