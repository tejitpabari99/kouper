from fastapi import APIRouter, Query
from typing import Optional
from ..data.providers import PROVIDERS
from ..logic.availability import check_availability

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
def list_providers(
    specialty: Optional[str] = Query(None, description="Filter by specialty (case-insensitive)"),
    q: Optional[str] = Query(None, description="Fuzzy search by provider full name (substring, case-insensitive)"),
):
    results = []

    for provider in PROVIDERS:
        # Filter by specialty if provided
        if specialty and provider.specialty.lower() != specialty.lower():
            continue

        # Filter by name query if provided (case-insensitive substring match)
        if q and q.lower() not in provider.full_name.lower():
            continue

        # Use check_availability to build location data
        try:
            availability = check_availability(provider.full_name)
        except ValueError:
            continue

        locations = [
            {
                "name": loc.department_name,
                "days": loc.days,
                "hours": loc.hours,
                "address": loc.address,
                "phone": loc.phone,
            }
            for loc in availability.locations
        ]

        results.append({
            "name": provider.full_name,
            "specialty": provider.specialty,
            "locations": locations,
            "accepted_insurances": provider.accepted_insurances,
            "accepting_new_patients": provider.accepting_new_patients,
            "waitlist_available": provider.waitlist_available,
        })

    return results
