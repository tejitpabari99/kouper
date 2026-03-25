"""
Co-location detection for same-day scheduling optimization.

When a patient has multiple referrals, booking providers who share a physical
location on the same day reduces patient travel burden.  This module identifies
those opportunities by matching provider names against the PROVIDERS list and
grouping by department (location).
"""
from typing import List, Dict, Tuple
from collections import defaultdict
from pydantic import BaseModel
from ..data.providers import PROVIDERS


class ColocationSuggestion(BaseModel):
    location_name: str
    address: str
    providers: List[str]    # display names e.g. ["Dr. Gregory House", "Dr. Temperance Brennan"]
    specialties: List[str]
    message: str


def _format_provider_name(raw_name: str) -> str:
    """Convert 'House, Gregory MD' → 'Dr. Gregory House'"""
    # Strip cert (MD, PhD, FNP etc), split on comma, reverse order, prepend Dr.
    # Handle cases like "Brennan, Temperance PhD, MD" or "Perry, Chris FNP"
    parts = raw_name.strip().split(",")
    if len(parts) < 2:
        return f"Dr. {raw_name.strip()}"
    last = parts[0].strip()
    # Everything after the first comma is first name + optional certifications
    rest = ",".join(parts[1:]).strip()
    # Remove certification suffixes (words that are all caps or known certs)
    cert_keywords = {"MD", "PHD", "FNP", "DO", "PA", "NP", "RN", "DNP", "DPM", "DDS", "DVM", "PHARMD"}
    # Join all parts after the last_name comma, then split on whitespace
    # "Temperance PhD, MD" → tokens ["Temperance", "PhD,", "MD"]
    rest_tokens = rest.split()
    first_tokens = []
    for token in rest_tokens:
        cleaned = token.strip(".,").upper()
        if cleaned in cert_keywords:
            break
        first_tokens.append(token.strip(".,"))
    first = " ".join(first_tokens).strip() if first_tokens else rest_tokens[0].strip(".,") if rest_tokens else ""
    return f"Dr. {first} {last}"


def find_colocated_providers(provider_names: List[str]) -> List[ColocationSuggestion]:
    """
    Given a list of provider display names, find any that share a physical location.
    Returns one ColocationSuggestion per shared location with 2+ providers.
    Pure function — reads only from in-memory PROVIDERS list.
    """
    # Step 1: For each name in provider_names, find matching providers in PROVIDERS
    matched: List[Tuple[str, str]] = []  # (formatted_display_name, specialty)
    matched_by_dept: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    # dept_name -> [(display_name, specialty)]

    for input_name in provider_names:
        input_lower = input_name.lower()
        input_words = set(input_lower.replace(",", " ").split())

        for provider in PROVIDERS:
            provider_words = set(
                (provider.last_name + " " + provider.first_name).lower().split()
            )
            # Loose matching: any word overlap between input and provider name
            if input_words & provider_words:
                formatted = _format_provider_name(provider.display_name)
                specialty = provider.specialty
                for dept in provider.departments:
                    matched_by_dept[dept.name].append((formatted, specialty, dept.address))
                break  # only match each input_name to one provider

    # Step 2: For each location with 2+ distinct providers, create a ColocationSuggestion
    suggestions = []
    for dept_name, entries in matched_by_dept.items():
        # Deduplicate by display_name
        seen_names = {}
        for display_name, specialty, address in entries:
            if display_name not in seen_names:
                seen_names[display_name] = (specialty, address)

        if len(seen_names) >= 2:
            provider_list = list(seen_names.keys())
            specialties = [seen_names[n][0] for n in provider_list]
            address = list(seen_names.values())[0][1]

            # Build message
            if len(provider_list) == 2:
                p1, p2 = provider_list[0], provider_list[1]
            else:
                p1 = provider_list[0]
                p2 = " and ".join(provider_list[1:])

            message = (
                f"Consider booking same-day at {dept_name} — "
                f"{p1} and {p2} both practice there. "
                f"This could save the patient a second trip."
            )

            suggestions.append(ColocationSuggestion(
                location_name=dept_name,
                address=address,
                providers=provider_list,
                specialties=specialties,
                message=message,
            ))

    return suggestions
