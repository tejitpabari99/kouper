"""
Provider and department data models.

Providers are defined in data/providers.py and loaded into memory at startup.
Each provider can practice at multiple departments (locations).
"""
from pydantic import BaseModel
from typing import List


class Department(BaseModel):
    """One physical practice location for a provider."""
    name: str
    phone: str
    address: str
    hours: str   # e.g. "M-F 9am-5pm" — parsed by availability.py


class Provider(BaseModel):
    """
    A specialist or PCP in the care coordinator's network.

    accepted_insurances is provider-specific and checked before the global
    ACCEPTED_INSURANCES list in insurance.py.  An empty list means the global
    list is used as a fallback.
    """
    last_name: str
    first_name: str
    certification: str
    specialty: str
    departments: List[Department]
    accepted_insurances: List[str] = []
    accepting_new_patients: bool = True
    waitlist_available: bool = False

    @property
    def full_name(self) -> str:
        return f"Dr. {self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        """Last, First Cert format — used for the system prompt provider directory."""
        return f"{self.last_name}, {self.first_name} {self.certification}"
