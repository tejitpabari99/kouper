"""
Provider availability logic — parses hours strings into structured day/time data.

Provider hours are stored as compact strings like "M-W 9am-5pm" or "Th-F 10am-4pm".
This module parses those strings into lists of full weekday names and time ranges
for display in the UI and for slot generation.
"""
from typing import List, Optional

from app.models.appointment import AvailabilityResult, DepartmentAvailability
from app.models.provider import Provider
from app.data.providers import PROVIDERS

# Ordered list of weekday abbreviations mapping to full names
DAY_ORDER = ["M", "Tu", "W", "Th", "F"]
DAY_NAMES = {
    "M": "Monday",
    "Tu": "Tuesday",
    "W": "Wednesday",
    "Th": "Thursday",
    "F": "Friday",
}


def _parse_days(hours_str: str) -> List[str]:
    """
    Parse the day portion of an hours string like 'M-W 9am-5pm' or 'Tu-Th 10am-4pm'.
    Returns a list of full weekday names.
    """
    # Split on space to isolate the day range (first token)
    day_part = hours_str.split()[0]  # e.g. "M-W" or "Tu-Th" or "M-F"

    if "-" in day_part:
        start_abbr, end_abbr = day_part.split("-", 1)
        start_idx = DAY_ORDER.index(start_abbr)
        end_idx = DAY_ORDER.index(end_abbr)
        return [DAY_NAMES[DAY_ORDER[i]] for i in range(start_idx, end_idx + 1)]
    else:
        # Single day
        return [DAY_NAMES[day_part]]


def _parse_hours_time(hours_str: str) -> str:
    """Extract the time portion from an hours string like 'M-W 9am-5pm' → '9am-5pm'."""
    parts = hours_str.split()
    if len(parts) >= 2:
        return parts[1]
    return hours_str


def _normalize_provider_name(name: str):
    """
    Normalize a provider name into (first_name, last_name).
    Handles:
      - "Dr. Gregory House"
      - "Gregory House"
      - "House, Gregory"
      - "House, Gregory MD"
    Returns (first_name, last_name) tuple, both lowercased.
    """
    name = name.strip()

    # Remove "Dr." prefix
    if name.startswith("Dr."):
        name = name[3:].strip()

    # Handle "Last, First [Credential]" format
    if "," in name:
        parts = name.split(",", 1)
        last_name = parts[0].strip()
        # Take only the first word of the remainder (ignore credentials like MD)
        first_name = parts[1].strip().split()[0]
        return first_name.lower(), last_name.lower()

    # Handle "First Last" format — take first two words
    parts = name.split()
    if len(parts) >= 2:
        return parts[0].lower(), parts[1].lower()

    return name.lower(), ""


def _find_provider(provider_name: str) -> Optional[Provider]:
    """Find a provider by name, supporting multiple name formats."""
    first, last = _normalize_provider_name(provider_name)
    for provider in PROVIDERS:
        if (
            provider.first_name.lower() == first
            and provider.last_name.lower() == last
        ):
            return provider
    return None


def check_availability(provider_name: str) -> AvailabilityResult:
    """
    Return availability for all departments of the given provider.
    provider_name can be in any of these formats:
      - "House, Gregory"
      - "Gregory House"
      - "Dr. Gregory House"
    """
    provider = _find_provider(provider_name)
    if provider is None:
        raise ValueError(f"Provider not found: {provider_name!r}")

    locations: List[DepartmentAvailability] = []
    for dept in provider.departments:
        days = _parse_days(dept.hours)
        hours_time = _parse_hours_time(dept.hours)
        locations.append(
            DepartmentAvailability(
                department_name=dept.name,
                days=days,
                hours=hours_time,
                phone=dept.phone,
                address=dept.address,
            )
        )

    return AvailabilityResult(
        provider_name=provider.full_name,
        specialty=provider.specialty,
        locations=locations,
    )
