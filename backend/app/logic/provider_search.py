"""
Provider lookup logic.

Thin query layer over the in-memory PROVIDERS data list.  Currently backed by
a static data file; could be replaced with a real database query without
changing any callers.
"""
from typing import List

from app.models.provider import Provider
from app.data.providers import PROVIDERS


def get_providers(specialty: str) -> List[Provider]:
    """
    Return all providers whose specialty matches the given string.
    Matching is case-insensitive to tolerate LLM capitalization variation
    (e.g. "orthopedics" vs "Orthopedics").
    """
    specialty_lower = specialty.strip().lower()
    return [p for p in PROVIDERS if p.specialty.lower() == specialty_lower]
