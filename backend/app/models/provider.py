from pydantic import BaseModel
from typing import List


class Department(BaseModel):
    name: str
    phone: str
    address: str
    hours: str   # e.g. "M-F 9am-5pm"


class Provider(BaseModel):
    last_name: str
    first_name: str
    certification: str
    specialty: str
    departments: List[Department]

    @property
    def full_name(self) -> str:
        return f"Dr. {self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        return f"{self.last_name}, {self.first_name} {self.certification}"
