from fastapi import APIRouter
import random

router = APIRouter(tags=["distance"])

@router.get("/distance")
def get_distance(from_address: str = "", provider_address: str = ""):
    """Return a mock driving distance between two addresses."""
    # Mock: generate a plausible distance based on string length heuristic
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
