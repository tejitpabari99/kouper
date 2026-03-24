from fastapi import APIRouter
from ..data.transport_resources import TRANSPORT_RESOURCES

router = APIRouter(tags=["transport"])

@router.get("/transport-resources")
def get_transport_resources():
    """Return all community transportation resources for care coordinator reference."""
    return TRANSPORT_RESOURCES
