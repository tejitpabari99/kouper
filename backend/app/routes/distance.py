"""
Distance estimation route (stub).

Returns a mock driving distance and time between two addresses.  A real
implementation would call a mapping API (Google Maps, MapBox).  The current
implementation seeds a random number generator from the address string lengths
to produce consistent results for the same pair of addresses without any
external dependency.
"""
from fastapi import APIRouter
import random

router = APIRouter(tags=["distance"])

@router.get("/distance")
def get_distance(from_address: str = "", provider_address: str = ""):
    """Return a mock driving distance between two addresses."""
    # Seed from address lengths so the same address pair always returns the
    # same estimate — consistent enough for UI display without a real API key.
    seed = len(from_address) + len(provider_address)
    random.seed(seed)
    miles = round(random.uniform(1.2, 24.8), 1)
    minutes = int(miles * 2.8 + random.uniform(3, 12))
    return {
        "from_address": from_address,
        "provider_address": provider_address,
        "miles": miles,
        "drive_minutes": minutes,
        "note": "Mock distance — real map integration not yet connected"
    }
