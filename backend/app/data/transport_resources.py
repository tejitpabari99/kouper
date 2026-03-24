from typing import List, Optional, Literal
from pydantic import BaseModel


class TransportResource(BaseModel):
    name: str
    type: Literal["rideshare", "medicaid_transport", "volunteer", "transit"]
    phone: Optional[str] = None
    url: Optional[str] = None
    service_area: str
    notes: str


TRANSPORT_RESOURCES: List[TransportResource] = [
    TransportResource(
        name="NC MedAssist Transport",
        type="medicaid_transport",
        phone="1-800-555-0101",
        url=None,
        service_area="Statewide NC",
        notes="For Medicaid recipients only. Requires 48-hour advance booking.",
    ),
    TransportResource(
        name="Greensboro Urban Transit",
        type="transit",
        phone="(336) 555-0210",
        url=None,
        service_area="Greensboro, NC",
        notes="Fixed route. PPTH Orthopedics is on Route 12.",
    ),
    TransportResource(
        name="Guilford County Senior Services",
        type="volunteer",
        phone="(336) 555-0185",
        url=None,
        service_area="Guilford County, NC",
        notes="Free volunteer driver program. Patients 60+.",
    ),
    TransportResource(
        name="Lyft Healthcare",
        type="rideshare",
        phone=None,
        url="https://healthcare.lyft.com",
        service_area="Most NC metro areas",
        notes="Nurse can schedule a ride on behalf of patient via the Lyft Health portal.",
    ),
]
