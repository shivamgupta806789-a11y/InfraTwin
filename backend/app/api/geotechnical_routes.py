from fastapi import APIRouter, Query, HTTPException, status
from app.models.geotechnical import GeotechnicalSiteProfile
from app.services.geotechnical_service import GeotechnicalService

router = APIRouter(prefix="/api/v1/geotechnical", tags=["Geotechnical & Subsurface"])


@router.get("/profile", response_model=GeotechnicalSiteProfile)
async def get_geotechnical_profile(
    latitude: float = Query(default=28.6139, ge=-90.0, le=90.0, description="Site latitude in decimal degrees"),
    longitude: float = Query(default=77.2090, ge=-180.0, le=180.0, description="Site longitude in decimal degrees"),
    site_id: str = Query(default="site-001", description="Site identifier"),
):
    """
    Returns the subsurface geotechnical profile, soil stratigraphy layers,
    borehole logs, and seismic/geophysical hazard screening.
    """
    try:
        return GeotechnicalService.get_site_geotechnical_profile(
            lat=latitude,
            lon=longitude,
            site_id=site_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate geotechnical profile: {str(e)}"
        )
