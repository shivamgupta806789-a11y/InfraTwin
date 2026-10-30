from fastapi import APIRouter, Query, HTTPException, status
from app.models.sustainability import SustainabilityAuditReport
from app.services.sustainability_service import SustainabilityRecommendationService

router = APIRouter(prefix="/api/v1/sustainability", tags=["Comprehensive Sustainability Intelligence"])


@router.get("/report", response_model=SustainabilityAuditReport)
async def get_sustainability_report(
    target_entity_id: str = Query(default="sample-office-twin", description="Building ID, Site ID, or City ID"),
    level: str = Query(default="building", description="'city', 'district', 'site', 'building', or 'element'"),
    latitude: float = Query(default=28.6139, ge=-90.0, le=90.0),
    longitude: float = Query(default=77.2090, ge=-180.0, le=180.0)
):
    """
    Evaluates comprehensive recommendations across 5 pillars:
    A. Environmental Sustainability
    B. Geotechnical & Site Suitability
    C. Infrastructure Resilience
    D. Urban Planning
    E. Lifecycle & Future Risk
    """
    try:
        return SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
            target_entity_id=target_entity_id,
            level=level,
            latitude=latitude,
            longitude=longitude
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sustainability intelligence report: {str(e)}"
        )
