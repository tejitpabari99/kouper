from typing import List

from app.models.provider import Provider
from app.data.providers import PROVIDERS


def get_providers(specialty: str) -> List[Provider]:
    """
    Return all providers whose specialty matches the given string.
    Matching is case-insensitive.
    """
    specialty_lower = specialty.strip().lower()
    return [p for p in PROVIDERS if p.specialty.lower() == specialty_lower]
