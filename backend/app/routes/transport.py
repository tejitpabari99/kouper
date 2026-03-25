"""
Transportation resources route.

Returns the static list of community transportation options available to
patients (e.g. medical transport services, bus pass programs).  Shown when
the nurse marks that a patient has transportation needs in their preferences.
"""
from fastapi import APIRouter
from ..data.transport_resources import TRANSPORT_RESOURCES

router = APIRouter(tags=["transport"])

@router.get("/transport-resources")
def get_transport_resources():
    """Return all community transportation resources for care coordinator reference."""
    return TRANSPORT_RESOURCES
