from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List

from app.models.geospatial_profile import UnifiedLocationProfile
from app.services.geospatial_integration_service import GeospatialIntegrationService
from app.services.dataset_registry import DatasetRegistryService
from app.services.sustainability_service import SustainabilityRecommendationService
from app.models.sustainability import SustainabilityAuditReport

router = APIRouter(prefix="/api/geospatial", tags=["Geospatial & Environmental Intelligence"])


@router.get("/location-profile", response_model=UnifiedLocationProfile)
def get_location_profile(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Project latitude in WGS84 coordinates"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Project longitude in WGS84 coordinates"),
    place_name: Optional[str] = Query(None, description="Optional human-readable project place name")
):
    """
    Retrieves and compiles a unified location profile synthesizing 10 Earth Observation,
    pedological, hydrological, and climatological datasets:
    1. ESA WorldCover 10m
    2. Dynamic World
    3. Copernicus Sentinel-2 L2A
    4. Global Forest Watch
    5. OpenStreetMap
    6. Microsoft Global ML Building Footprints
    7. SoilGrids 250m v2.0
    8. HydroSHEDS / HydroRIVERS
    9. NASA POWER
    10. ERA5 Atmospheric Reanalysis
    """
    try:
        profile = GeospatialIntegrationService.get_unified_location_profile(
            latitude=latitude,
            longitude=longitude,
            place_name=place_name
        )
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compile unified geospatial location profile: {str(e)}"
        )


@router.get("/datasets-registry")
def get_datasets_registry() -> Dict[str, Any]:
    """
    Returns governance metadata, source references, licensing, and ML task applicability
    for all candidate environmental and geospatial datasets.
    """
    datasets = DatasetRegistryService.list_all_datasets()
    governance = DatasetRegistryService.get_governance_summary()
    return {
        "datasets": [d.dict() for d in datasets],
        "governance": governance
    }


@router.get("/evaluate-multi-domain", response_model=SustainabilityAuditReport)
def evaluate_multi_domain(
    model_id: str = Query("sample-office-twin", description="Target IFC or parametric building model ID"),
    latitude: float = Query(28.6139, ge=-90.0, le=90.0),
    longitude: float = Query(77.2090, ge=-180.0, le=180.0)
):
    """
    Executes building-specific multi-domain recommendation generation combining
    building geometry with the 10 target geospatial and environmental datasets.
    """
    try:
        report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
            target_entity_id=model_id,
            level="building",
            latitude=latitude,
            longitude=longitude
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multi-domain evaluation failed: {str(e)}"
        )
